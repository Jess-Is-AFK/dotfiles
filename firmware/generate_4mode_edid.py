#!/usr/bin/env python3
import os
import struct

EDID_PATH = "/lib/firmware/edid/crt_15khz_multi.bin"

def make_dtd(pclk_khz, h_act, h_blank, h_fp, h_sync, v_act, v_blank, v_fp, v_sync, interlaced, h_pos=True, v_pos=True):
    dtd = bytearray(18)
    pclk_10k = pclk_khz // 10
    dtd[0] = pclk_10k & 0xFF
    dtd[1] = (pclk_10k >> 8) & 0xFF
    
    dtd[2] = h_act & 0xFF
    dtd[3] = h_blank & 0xFF
    dtd[4] = ((h_act >> 8) << 4) | ((h_blank >> 8) & 0x0F)
    
    dtd[5] = v_act & 0xFF
    dtd[6] = v_blank & 0xFF
    dtd[7] = ((v_act >> 8) << 4) | ((v_blank >> 8) & 0x0F)
    
    dtd[8] = h_fp & 0xFF
    dtd[9] = h_sync & 0xFF
    dtd[10] = ((v_fp & 0x0F) << 4) | (v_sync & 0x0F)
    dtd[11] = (((h_fp >> 8) & 0x03) << 6) | (((h_sync >> 8) & 0x03) << 4) | (((v_fp >> 8) & 0x03) << 2) | ((v_sync >> 8) & 0x03)
    
    # 400mm x 300mm (4:3 aspect ratio)
    dtd[12] = 400 & 0xFF
    dtd[13] = 300 & 0xFF
    dtd[14] = (((400 >> 8) & 0x0F) << 4) | ((300 >> 8) & 0x0F)
    
    flags = 0x18
    if h_pos: flags |= 0x02
    if v_pos: flags |= 0x04
    if interlaced: flags |= 0x80
    dtd[17] = flags
    return dtd

# 1. 8-byte Header
header = bytes([0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])

# 2. Vendor / Product: 'NAM', code 0, week 1, year 2020
vendor = struct.pack(">H", 0x39AC)
prod_code = struct.pack("<H", 0)
serial = struct.pack("<I", 0)
mfg_time = bytes([1, 30])

# 3. EDID 1.4, Analog video input, 0.7V/0.3V, separate sync
edid_ver = bytes([1, 4])
vid_input = bytes([0x0E])
screen_size = bytes([40, 30])
gamma = bytes([120])
features = bytes([0x0A])
color = bytes([0xEE, 0x91, 0xA3, 0x54, 0x4C, 0x99, 0x26, 0x0F, 0x50, 0x54])
est_timings = bytes([0x00, 0x00, 0x00])
std_timings = bytes([0x01, 0x01] * 8)

base = (
    header + vendor + prod_code + serial + mfg_time
    + edid_ver + vid_input + screen_size + gamma + features
    + color + est_timings + std_timings
)

# Slot 1: 640x480i @ 60Hz field rate (12.52 MHz, V_act=480, V_blank=45, V_total=525, Interlaced)
dtd1 = make_dtd(12520, 640, 156, 26, 58, 480, 45, 6, 6, interlaced=True)

# Slot 2: 320x240p @ 60Hz (6.25 MHz, V_act=240, V_blank=22, V_total=262, Progressive)
dtd2 = make_dtd(6250, 320, 78, 13, 29, 240, 22, 3, 3, interlaced=False)

# Slot 3: 2560x240p @ 60Hz (50.00 MHz, V_act=240, V_blank=22, V_total=262, Progressive)
dtd3 = make_dtd(50000, 2560, 624, 104, 232, 240, 22, 3, 3, interlaced=False)

# Slot 4: 2560x480i @ 60Hz field rate (50.10 MHz, V_act=480, V_blank=45, V_total=525, Interlaced)
dtd4 = make_dtd(50100, 2560, 624, 104, 232, 480, 45, 6, 6, interlaced=True)

edid = bytearray(base + dtd1 + dtd2 + dtd3 + dtd4)
edid.append(0x00)

checksum = (256 - (sum(edid) % 256)) % 256
edid.append(checksum)

assert len(edid) == 128, f"Error: EDID size is {len(edid)} bytes"

os.makedirs(os.path.dirname(EDID_PATH), exist_ok=True)
with open(EDID_PATH, "wb") as f:
    f.write(edid)

print(f"✅ Generated {EDID_PATH} (128 bytes, checksum=0x{checksum:02X})")
