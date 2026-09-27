#!/usr/bin/env python3
"""
generate_edid.py - 15kHz CRT Multi-Mode EDID Generator
Target: Olympus OEV-203 / Sony PVM via VGA2SCART on AMD Radeon (VGA-1)

Generates a VESA EDID 1.3/1.4 compliant 128-byte binary containing 4 DTDs:
  1. 2560x240p @ 60.11Hz (NTSC Progressive - Preferred)
  2. 2560x224p @ 60.11Hz (Centered Progressive)
  3. 2560x288p @ 50.00Hz (PAL Progressive)
  4. 2560x480i @ 60.00Hz (Interlaced)
"""

import os
import struct
import sys


def encode_dtd(
    pclk_khz,
    hact,
    hblank,
    hfp,
    hsync,
    vact,
    vblank,
    vfp,
    vsync,
    interlaced=False,
):
    """Encodes an 18-byte VESA Detailed Timing Descriptor (DTD)."""
    pclk_10khz = pclk_khz // 10
    pclk_bytes = struct.pack("<H", pclk_10khz)

    b2 = hact & 0xFF
    b3 = hblank & 0xFF
    b4 = ((hact >> 8) & 0x0F) << 4 | ((hblank >> 8) & 0x0F)

    b5 = vact & 0xFF
    b6 = vblank & 0xFF
    b7 = ((vact >> 8) & 0x0F) << 4 | ((vblank >> 8) & 0x0F)

    b8 = hfp & 0xFF
    b9 = hsync & 0xFF
    b10 = ((vfp & 0x0F) << 4) | (vsync & 0x0F)
    b11 = (
        (((hfp >> 8) & 0x03) << 6)
        | (((hsync >> 8) & 0x03) << 4)
        | (((vfp >> 4) & 0x03) << 2)
        | ((vsync >> 4) & 0x03)
    )

    # 4:3 Physical Image Size (400mm x 300mm)
    b12 = 400 & 0xFF
    b13 = 300 & 0xFF
    b14 = (((400 >> 8) & 0x0F) << 4) | ((300 >> 8) & 0x0F)

    # Flags: Separate Sync, +hsync +vsync for active XOR combiner (0x1E)
    flags = 0x18 | 0x06
    if interlaced:
        flags |= 0x80

    return pclk_bytes + bytes([
        b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, 0, 0, flags
    ])


def build_edid(output_path="crt_15khz_multi.bin"):
    # 1. Header (8 bytes)
    header = bytes([0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])

    # 2. Vendor / Product ID
    mfg_id = bytes([0x10, 0xAC])  # 'DEL' vendor code
    prod_code = struct.pack("<H", 0x19F1)
    serial = struct.pack("<I", 0x41463249)

    # 3. Structure Version 1, Revision 3 & Basic Display Parameters
    meta = bytes()

    # 4. Color Characteristics
    color = bytes(
        [0xA5, 0x30, 0x1B, 0x78, 0x3A, 0xB6, 0x75, 0xA6, 0x55, 0x52]
    )

    # 5. Established Timings (suppressed standard 31kHz PC modes)
    est = bytes([0x00, 0x00, 0x00])

    # 6. Standard Timings (unused slots: 0x01, 0x01)
    std = bytes([0x01, 0x01] * 8)

    # 7. Detailed Timing Descriptors (4 x 18 bytes)
    # DTD 1: 2560x240p @ 60.11Hz Progressive (+hsync +vsync) [Preferred]
    dtd1 = encode_dtd(50400, 2560, 640, 80, 240, 240, 22, 4, 3, False)

    # DTD 2: 2560x224p @ 60.11Hz Progressive (+hsync +vsync)
    dtd2 = encode_dtd(50400, 2560, 640, 80, 240, 224, 38, 12, 3, False)

    # DTD 3: 2560x288p @ 50.00Hz PAL Progressive (+hsync +vsync)
    dtd3 = encode_dtd(49920, 2560, 640, 80, 240, 288, 24, 2, 3, False)

    # DTD 4: 2560x480i @ 60.00Hz Interlaced (+hsync +vsync, Flags: 0x9E)
    dtd4 = encode_dtd(50400, 2560, 640, 80, 240, 480, 45, 9, 6, True)

    # 8. Extension Flag & Checksum Calculation
    raw = (
        header
        + mfg_id
        + prod_code
        + serial
        + meta
        + color
        + est
        + std
        + dtd1
        + dtd2
        + dtd3
        + dtd4
        + bytes([0x00])
    )
    checksum = (256 - (sum(raw) % 256)) % 256
    full_edid = raw + bytes([checksum])

    with open(output_path, "wb") as f:
        f.write(full_edid)

    print(f"✓ Generated {output_path} ({len(full_edid)} bytes)")
    print(f"  Checksum: {hex(checksum)} (Valid: {sum(full_edid) % 256 == 0})")
    print("  Modes included:")
    print("    1. 2560x240p @ 60.11Hz (NTSC Progressive - Preferred)")
    print("    2. 2560x224p @ 60.11Hz (NTSC Progressive)")
    print("    3. 2560x288p @ 50.00Hz (PAL Progressive)")
    print("    4. 2560x480i @ 60.00Hz (NTSC Interlaced)")


if __name__ == "__main__":
    out_file = sys.argv if len(sys.argv) > 1 else "crt_15khz_multi.bin"
    build_edid(out_file)
