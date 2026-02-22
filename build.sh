#!/bin/bash
# Build WinRA.app, WinRA.dmg, and WinRA.pkg for macOS distribution
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="WinRA"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON="$VENV_DIR/bin/python3"
PIP="$VENV_DIR/bin/pip"
PYINSTALLER="$VENV_DIR/bin/pyinstaller"

echo "=== WinRA Build Script ==="
echo ""

# Check venv
if [ ! -f "$PYTHON" ]; then
    echo "ERROR: Virtual environment tidak ditemukan di $VENV_DIR"
    echo "Jalankan: python3.13 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check PyInstaller
if [ ! -f "$PYINSTALLER" ]; then
    echo "Installing PyInstaller..."
    "$PIP" install pyinstaller
fi

echo "1/5 - Cleaning previous build..."
rm -rf build dist "${APP_NAME}.dmg" "${APP_NAME}.pkg"

echo "2/5 - Building ${APP_NAME}.app with PyInstaller..."
"$PYINSTALLER" \
    --name "$APP_NAME" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "app:app" \
    --hidden-import customtkinter \
    --hidden-import PIL \
    --hidden-import rarfile \
    --hidden-import darkdetect \
    --collect-all customtkinter \
    main.py

echo ""
echo "   ✅ ${APP_NAME}.app created at: dist/${APP_NAME}.app"

echo "3/5 - Creating ${APP_NAME}.dmg..."

# Create a temporary directory for DMG contents
DMG_DIR="$SCRIPT_DIR/dmg_contents"
rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"

# Copy .app to DMG directory
cp -R "dist/${APP_NAME}.app" "$DMG_DIR/"

# Create a symlink to Applications
ln -s /Applications "$DMG_DIR/Applications"

# Create DMG using hdiutil
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov \
    -format UDZO \
    "${APP_NAME}.dmg"

# Cleanup
rm -rf "$DMG_DIR"

echo "4/5 - Signing app..."
xattr -cr "dist/${APP_NAME}.app"
codesign -s - --force --all-architectures --timestamp --deep \
    "dist/${APP_NAME}.app" 2>/dev/null || true

echo "5/5 - Creating ${APP_NAME}.pkg installer..."
bash "$SCRIPT_DIR/build_pkg.sh"

echo ""
echo "=== Build Complete ==="
echo "📦 App:       dist/${APP_NAME}.app"
echo "💿 DMG:       ${APP_NAME}.dmg"
echo "📀 Installer: ${APP_NAME}.pkg"
echo ""
echo "Untuk menjalankan:  open dist/${APP_NAME}.app"
echo "Untuk distribusi:"
echo "  DMG (drag & drop): kirim file ${APP_NAME}.dmg"
echo "  PKG (installer):   kirim file ${APP_NAME}.pkg"
