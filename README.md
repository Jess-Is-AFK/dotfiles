# Gentoo Dual-GPU + 15kHz Analog CRT Workstation Setup

A reproducible Gentoo Linux configuration for driving dual modern high-refresh flat panels alongside an analog 15kHz CRT (e.g., Olympus OEV-203 / Sony PVM) via an AMD Radeon RX 7900 XT and an AMD Radeon R5 430 OEM.

## Hardware Architecture
* **Primary GPU:** AMD Radeon RX 7900 XT (`/dev/dri/card0`)
  * `DP-2`: 2560x1440 @ 165Hz
  * `DP-3`: 2560x1440 @ 165Hz
* **Secondary GPU:** AMD Radeon R5 430 OEM (`/dev/dri/card1`)
  * `VGA-1`: 2560x240 @ 60.01Hz (via VGA2SCART sync combiner)
* **Target CRT:** Olympus OEV-203 (15.7 kHz RGB)

## Features
* **Unified Driver Stack:** Binds Southern Islands (GCN 1.0) to `amdgpu` alongside RDNA 3.
* **wlroots Multi-GPU:** Avoids Aquamarine cross-GPU blit failures by allocating linear buffers across PCIe.
* **Super-Resolution Modelines:** Custom 2560-wide EDID covering 240p, 224p, 480i, 288p, and 576i.
* **Workspace Pinning:** Workspaces 1–8 dedicated to flat panels; Workspace 9 pinned permanently to the PVM.
* **Automated Window Routing:** Emulators (DuckStation, RetroArch) automatically route and fullscreen on the PVM.

## Installation

1. **Clone and deploy symlinks:**
   ```bash
   git clone <your-repo-url> ~/dotfiles
   cd ~/dotfiles
   ./install.sh
   ```

2. **Kernel Configuration (`/usr/src/linux/.config`):**
   Ensure the options in `kernel/config-crt.snippet` are compiled into your kernel.

3. **GRUB Command Line (`/etc/default/grub`):**
   ```text
   GRUB_CMDLINE_LINUX_DEFAULT="radeon.si_support=0 amdgpu.si_support=1 drm.edid_firmware=VGA-1:edid/2560x240.bin video=VGA-1:2560x240@60eS"
   ```
   Regenerate GRUB: `sudo grub-mkconfig -o /boot/grub/grub.cfg`

4. **Launch Sway:**
   ```bash
   start-sway
   ```
