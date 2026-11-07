# Halcyon — Gentoo Dual-GPU 15kHz CRT & Multi-Head Wayland Workstation

A reproducible Gentoo Linux configuration driving dual high-refresh 1440p desktop monitors alongside an analog 15kHz CRT (Olympus OEV-203 / Sony PVM) under a unified, multi-GPU Sway (Wayland) session.

---

## 1. Hardware Architecture

~~~text
[AMD Ryzen 9 7950X] -- PCIe
         |
         +-- [AMD Radeon RX 7900 XT] (0000:03:00.0) -- DP-1 / DP-2 --> 2x 1440p @ 165Hz (Desktop)
         |
         +-- [AMD Radeon R5 430 OEM] (0000:04:00.0) -- VGA-1 --------> [VGA2SCART] --> [Olympus OEV-203] (15kHz RGB)
~~~

* **Primary Compute / Desktop GPU:** AMD Radeon RX 7900 XT (`amdgpu`, Navi 31)
  * `DP-1`: $2560 \times 1440$ @ $165\text{ Hz}$ (Primary desktop canvas, pos: `0 0`)
  * `DP-2`: $2560 \times 1440$ @ $165\text{ Hz}$ (Secondary desktop canvas, pos: `2560 0`)
* **Secondary CRT Video Sink:** AMD Radeon R5 430 OEM (`amdgpu`, GCN 1.0 / Oland)
  * `VGA-1`: Analog RGBHV output forced onto the `amdgpu` driver stack (pos: `0 1440`)
* **Sync Combiner:** Retro Upgrades VGA2SCART Active Adapter
  * Hardware XOR logic gate combiner; **strictly requires positive sync (`+hsync +vsync`)** on all modelines to synthesize clean CSYNC.
* **Target CRT Monitor:** Olympus OEV-203 (Sony PVM-20M2MDU medical chassis) set to `RGB-EXT SYNC`.
* **Audio:** Realtek ALC897 analog codec configured for simultaneous front-panel headphone and rear motherboard line-out playback, balanced via physical volume controls.
* **Gamepad:** 8BitDo Ultimate 2 Wireless controller (XInput via `xpad`, background polling enabled).

---

## 2. Key Architectural Features

* **Low Dot-Clock Native 4:3 Modes (No Gamescope Scaling):**
  * Kernel patched with `linux_kernel_15khz` PLL and DCE fixes, unlocking pixel clocks down to $6.25\text{ MHz}$ (`320x240p`) and $12.50\text{ MHz}$ (`640x480i`).
  * Emulators, PC ports, and frontends render directly onto native 4:3 raster grids with zero horizontal squishing or bilinear blur.
* **Patched wlroots Interlaced Support:**
  * `gui-libs/wlroots` patched via `/etc/portage/patches/gui-libs/wlroots/allow-interlace.patch` to expose interlaced `480i` modes inside Sway.
* **4-Mode Custom 128-Byte EDID:**
  * Packed into `/lib/firmware/edid/15khz_dual.bin` and embedded into the Dracut initramfs for early KMS attachment:
    * **Slot 1 (Preferred):** `640x480i` @ $60\text{ Hz}$ ($12.50\text{ MHz}$, `+hsync +vsync`)
    * **Slot 2:** `320x240p` @ $60\text{ Hz}$ ($6.25\text{ MHz}$, `+hsync +vsync`)
    * **Slot 3:** `2560x240p` @ $60\text{ Hz}$ ($50.00\text{ MHz}$, super-resolution fallback)
    * **Slot 4:** `2560x480i` @ $60\text{ Hz}$ ($50.00\text{ MHz}$, super-resolution fallback)
* **Hybrid Multi-Head Ergonomics:**
  * Seamless cross-screen mouse boundary: the cursor glides vertically between the 1440p desktop and the 240p/480i CRT screen.
  * Seat pointer constraints disabled (`seat * pointer_constraint disable`) so emulators never capture or trap the cursor.
  * `SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1` allows controller navigation in ES-DE or emulators while keyboard/mouse focus remains on the desktop.
* **Desktop-Isolated Waybar:**
  * Waybar is explicitly pinned to `DP-1` and `DP-2`, keeping the CRT canvas 100% borderless and free of status bar occlusion.

---

## 3. Repository Structure

~~~text
~/dotfiles/
|-- .config/
|   |-- sway/
|   |   `-- config              # Sway output topology, workspace 10 binding, window routing
|   `-- waybar/
|       |-- config.jsonc        # Desktop-filtered bar config (DP-1, DP-2 only)
|       `-- style.css           # Waybar dark minimal styling
|-- .local/
|   `-- bin/
|       |-- crt-run             # Dynamic pre/post mode switching wrapper (320x240 <-> 640x480)
|       |-- launch-es-de        # EmulationStation Desktop Edition 240p launcher
|       |-- launch-soh          # Ship of Harkinian native launcher
|       |-- launch-ps2          # PCSX2 480i launcher (Flatpak)
|       |-- launch-project-plus # Dolphin / Project+ 480i launcher (Flatpak)
|       |-- launch-steam-bpm    # Steam Big Picture 4:3 Gamescope container (Flatpak)
|       `-- crt-audio           # ALSA hardware audio mixer utility
|-- firmware/
|   `-- generate_4mode_edid.py  # Python generator for 128-byte positive-sync EDID
`-- gentoo/
    |-- kernel/                 # Kernel config snippets (amdgpu SI/CIK, xpad, uinput)
    `-- patches/                # wlroots allow-interlace patch
~~~

---

## 4. Boot & Kernel Configuration

### Kernel Parameters (`rEFInd` / `GRUB`)

~~~text
radeon.si_support=0 radeon.cik_support=0 amdgpu.si_support=1 amdgpu.cik_support=1 drm.edid_firmware=VGA-1:edid/15khz_dual.bin video=VGA-1:e
~~~

### Dracut Early KMS Bundling

The EDID binary is bundled directly into the initramfs image so early KMS initializes the 15kHz display pipeline and attaches positive-sync timings before the Wayland compositor loads:

~~~bash
sudo dracut --kver <KERNEL_VERSION> --force --include /lib/firmware/edid /lib/firmware/edid
~~~

### Audio Persistence (OpenRC)

Simultaneous front/rear analog output (`Auto-Mute Mode: Disabled`) is stored via `sudo alsactl store` and restored automatically at boot:

~~~bash
sudo rc-update add alsasound boot
~~~

---

## 5. Usage & Shortcuts

### Sway Display Controls

| Keybinding | Action |
| :--- | :--- |
| `$mod + 0` | Focus CRT workspace (Workspace 10) |
| `$mod + Shift + 0` | Move focused window to CRT |
| `$mod + Shift + F1` | Force `VGA-1` into `320x240p` (Progressive Scanlines) |
| `$mod + Shift + F2` | Force `VGA-1` into `640x480i` (Interlaced Text/Precision) |
| `$mod + Shift + g` | Launch ES-DE on demand on Workspace 10 |

### Standalone Launch Wrappers

~~~bash
# Run any arbitrary command wrapped in a temporary mode switch
crt-run 640x480 <command>

# Launchers
launch-es-de          # Boots ES-DE at 320x240p
launch-ps2            # Boots PCSX2 at 640x480i
launch-project-plus   # Boots Project+ Dolphin at 640x480i
launch-soh            # Boots Ship of Harkinian at 320x240p
launch-steam-bpm      # Boots Steam Big Picture scaled into 480i
~~~