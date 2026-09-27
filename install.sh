#!/usr/bin/env bash
set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME"

echo "=== Deploying Workstation Dotfiles ==="

# 1. Clean up legacy top-level symlinks and artifacts in ~
rm -f "$TARGET_DIR/bin" "$TARGET_DIR/foot" "$TARGET_DIR/fuzzel" "$TARGET_DIR/sway"
rm -f "$TARGET_DIR/320x240" "$TARGET_DIR/Using" "$TARGET_DIR/Warning:"

# 2. Ensure base directories exist
mkdir -p "$TARGET_DIR/.config" "$TARGET_DIR/appimages" "$TARGET_DIR/Pictures/Screenshots"

# 3. Direct symlinks for ~/.local/bin
mkdir -p "$TARGET_DIR/.local"
[ -d "$TARGET_DIR/.local/bin" ] && [ ! -L "$TARGET_DIR/.local/bin" ] && rm -rf "$TARGET_DIR/.local/bin"
ln -sfn "$DOTFILES_DIR/.local/bin" "$TARGET_DIR/.local/bin"
ln -sfn "$TARGET_DIR/.local/bin" "$TARGET_DIR/bin"

# 4. Direct symlinks for ~/.config apps
for app in sway fuzzel foot mako; do
    if [ -d "$DOTFILES_DIR/.config/$app" ]; then
        [ -d "$TARGET_DIR/.config/$app" ] && [ ! -L "$TARGET_DIR/.config/$app" ] && rm -rf "$TARGET_DIR/.config/$app"
        ln -sfn "$DOTFILES_DIR/.config/$app" "$TARGET_DIR/.config/$app"
        echo "✓ Linked ~/.config/$app -> $DOTFILES_DIR/.config/$app"
    fi
done

# 5. Ensure scripts are executable inside repo
chmod +x "$DOTFILES_DIR/.local/bin/"* 2>/dev/null || true
chmod +x "$DOTFILES_DIR/kernel/edid/generate_edid.py" 2>/dev/null || true

# 6. Check firmware
FIRMWARE_TARGET="/lib/firmware/edid/crt_15khz_multi.bin"
if [ ! -f "$FIRMWARE_TARGET" ]; then
    echo "⚠️  $FIRMWARE_TARGET not found. Generating..."
    python3 "$DOTFILES_DIR/kernel/edid/generate_edid.py" --modes all -o "$DOTFILES_DIR/kernel/edid/crt_15khz_multi.bin"
    sudo mkdir -p /lib/firmware/edid
    sudo cp "$DOTFILES_DIR/kernel/edid/crt_15khz_multi.bin" /lib/firmware/edid/
    echo "✓ Installed $FIRMWARE_TARGET"
fi

echo "✓ Deployment complete."
