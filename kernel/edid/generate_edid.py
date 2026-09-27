#!/usr/bin/env python3
"""
Universal 15kHz CRT EDID Generator for Retro Gaming & PVMs.
Supports custom modelines across classic consoles (240p, 224p, 480i, 288p, 576i).
Outputs compliant 128-byte (Base) or 256-byte (Base + CTA-861 Extension) EDID binaries.
"""
import sys
import argparse

# 15kHz CRT Modelines
# 2560 width provides exact integer/subpixel scaling for 256, 320, 384, 512, and 640 native widths.
TIMING_PRESETS = {
    "240p": {
        "name": "2560x240p @ 60.01Hz (NTSC Full)",
        "w": 2560, "h": 240,
        "h_fp": 104, "h_sync": 232, "h_bp": 288,
        "v_fp": 3, "v_sync": 3, "v_bp": 16,
        "clk_khz": 50060,
        "interlaced": False,
        "consoles": "Sony PlayStation 1, Nintendo 64, Sega Saturn (240p), PC Engine/TG16"
    },
    "224p": {
        "name": "2560x224p @ 60.01Hz (NTSC Active Scanlines)",
        "w": 2560, "h": 224,
        "h_fp": 104, "h_sync": 232, "h_bp": 288,
        "v_fp": 11, "v_sync": 3, "v_bp": 24,
        "clk_khz": 50060,
        "interlaced": False,
        "consoles": "Super Nintendo (SNES), Sega Genesis / Mega Drive, NES, Neo Geo MVS/AES, Capcom CPS1/2/3"
    },
    "480i": {
        "name": "2560x480i @ 60.01Hz (NTSC Interlaced)",
        "w": 2560, "h": 240,  # 240 lines per field = 480i
        "h_fp": 104, "h_sync": 232, "h_bp": 288,
        "v_fp": 3, "v_sync": 3, "v_bp": 16,
        "clk_khz": 50060,
        "interlaced": True,
        "consoles": "PS2, GameCube, Sega Dreamcast (15kHz), PS1 hi-res menus (Gran Turismo, Chrono Cross), Saturn 480i"
    },
    "288p": {
        "name": "2560x288p @ 50.09Hz (PAL Full)",
        "w": 2560, "h": 288,
        "h_fp": 104, "h_sync": 232, "h_bp": 288,
        "v_fp": 3, "v_sync": 3, "v_bp": 18,
        "clk_khz": 49760,
        "interlaced": False,
        "consoles": "European PAL consoles (PAL PS1, PAL SNES, PAL Mega Drive, Commodore Amiga)"
    },
    "576i": {
        "name": "2560x576i @ 50.09Hz (PAL Interlaced)",
        "w": 2560, "h": 288,  # 288 lines per field = 576i
        "h_fp": 104, "h_sync": 232, "h_bp": 288,
        "v_fp": 3, "v_sync": 3, "v_bp": 18,
        "clk_khz": 49760,
        "interlaced": True,
        "consoles": "European PAL PS2, GameCube, Wii on 15kHz RGB SCART"
    }
}

def build_dtd(preset):
    desc = bytearray(18)
    clock_10khz = round(preset["clk_khz"] / 10)
    desc[0] = clock_10khz & 0xFF
    desc[1] = (clock_10khz >> 8) & 0xFF

    h_act = preset["w"]
    h_blk = preset["h_fp"] + preset["h_sync"] + preset["h_bp"]
    desc[2] = h_act & 0xFF
    desc[3] = h_blk & 0xFF
    desc[4] = ((h_act >> 8) & 0x0F) << 4 | ((h_blk >> 8) & 0x0F)

    v_act = preset["h"]
    v_blk = preset["v_fp"] + preset["v_sync"] + preset["v_bp"]
    desc[5] = v_act & 0xFF
    desc[6] = v_blk & 0xFF
    desc[7] = ((v_act >> 8) & 0x0F) << 4 | ((v_blk >> 8) & 0x0F)

    desc[8] = preset["h_fp"] & 0xFF
    desc[9] = preset["h_sync"] & 0xFF
    desc[10] = ((preset["v_fp"] & 0x0F) << 4) | (preset["v_sync"] & 0x0F)
    desc[11] = (
        ((preset["h_fp"] >> 8) & 0x03) << 6
        | ((preset["h_sync"] >> 8) & 0x03) << 4
        | ((preset["v_fp"] >> 4) & 0x03) << 2
        | ((preset["v_sync"] >> 4) & 0x03)
    )

    desc[12] = 400 & 0xFF  # 400mm H-size
    desc[13] = 300 & 0xFF  # 300mm V-size
    desc[14] = ((400 >> 8) & 0x0F) << 4 | ((300 >> 8) & 0x0F)

    flags = 0x18
    if preset["interlaced"]:
        flags |= 0x80
    desc[17] = flags
    return desc

def build_name_desc(name):
    desc = bytearray(18)
    desc[3] = 0xFC
    name_bytes = name.encode("ascii")[:13]
    name_field = name_bytes.ljust(13, b' ')
    if len(name_bytes) < 13:
        name_field = name_bytes + b'\n' + b' ' * (12 - len(name_bytes))
    desc[5:18] = name_field
    return desc

def build_range_desc():
    desc = bytearray(18)
    desc[3] = 0xFD
    desc[5] = 48  # Min V (Hz)
    desc[6] = 65  # Max V (Hz)
    desc[7] = 14  # Min H (kHz)
    desc[8] = 17  # Max H (kHz)
    desc[9] = 6   # Max pixel clock (60 MHz / 10)
    desc[10] = 0x00
    desc[11:18] = b"\x0a\x20\x20\x20\x20\x20\x20"
    return desc

def generate_edid(selected_modes, output_file, monitor_name="Olympus OEV203"):
    if not selected_modes:
        selected_modes = ["240p", "224p", "480i"]

    base = bytearray(128)
    base[0:8] = b"\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00"
    base[8:10] = b"\x10\xac"
    base[10:12] = b"\x19\xf1"
    base[12:16] = b"\x49\x32\x46\x41"
    base[16] = 28
    base[17] = 30
    base[18] = 1
    base[19] = 3
    base[20] = 0x6D  # Analog input, separate sync
    base[21] = 40
    base[22] = 30
    base[23] = 120
    base[24] = 0x0A
    base[25:35] = b"\xa5\x30\x1b\x78\x3a\xb6\x75\xa6\x55\x52"
    base[38:54] = b"\x01\x01" * 8

    base_modes = selected_modes[:2]
    ext_modes = selected_modes[2:]

    if len(base_modes) >= 1:
        base[54:72] = build_dtd(TIMING_PRESETS[base_modes[0]])
    if len(base_modes) >= 2:
        base[72:90] = build_dtd(TIMING_PRESETS[base_modes[1]])

    base[90:108] = build_name_desc(monitor_name)
    base[108:126] = build_range_desc()

    base[126] = 1 if ext_modes else 0
    base[127] = (256 - (sum(base[:127]) % 256)) % 256

    final_data = bytearray(base)

    if ext_modes:
        ext = bytearray(128)
        ext[0] = 0x02  # CTA-861 tag
        ext[1] = 0x03  # Rev 3
        ext[2] = 0x04  # DTD offset
        ext[3] = 0x00

        offset = 4
        for m in ext_modes[:6]:
            ext[offset:offset+18] = build_dtd(TIMING_PRESETS[m])
            offset += 18

        ext[127] = (256 - (sum(ext[:127]) % 256)) % 256
        final_data.extend(ext)

    with open(output_file, "wb") as f:
        f.write(final_data)

    print(f"\n✓ Generated '{output_file}' ({len(final_data)} bytes)")
    print(f"  Checksum: Base={'Valid' if sum(final_data[:128])%256==0 else 'INVALID'}", end="")
    if len(final_data) > 128:
        print(f", Extension={'Valid' if sum(final_data[128:256])%256==0 else 'INVALID'}")
    else:
        print()
    print("  Active Modes Included:")
    for m in selected_modes:
        p = TIMING_PRESETS[m]
        print(f"   • {m.upper()}: {p['name']}")
        print(f"     Target: {p['consoles']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="15kHz CRT EDID Generator for Retro Gaming")
    parser.add_argument("-l", "--list", action="store_true", help="List all supported console presets")
    parser.add_argument("-m", "--modes", type=str, default="240p,224p,480i",
                        help="Comma-separated modes (e.g. '240p,224p,480i' or 'all')")
    parser.add_argument("-o", "--output", type=str, default="2560x240.bin", help="Output file path (.bin)")
    parser.add_argument("-n", "--name", type=str, default="Olympus OEV203", help="Monitor display name")

    args = parser.parse_args()

    if args.list:
        print("Supported 15kHz CRT Super-Resolution Modes:")
        print("=" * 80)
        for key, p in TIMING_PRESETS.items():
            print(f"{key.upper():<6} | {p['name']}")
            print(f"       | Compatible: {p['consoles']}")
            print("-" * 80)
        sys.exit(0)

    if args.modes.lower() == "all":
        modes_to_build = list(TIMING_PRESETS.keys())
    else:
        modes_to_build = [m.strip().lower() for m in args.modes.split(",") if m.strip().lower() in TIMING_PRESETS]

    generate_edid(modes_to_build, args.output, args.name)
