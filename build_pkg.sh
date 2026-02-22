#!/bin/bash
# Build WinRA.pkg installer for macOS
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="WinRA"
APP_PATH="dist/${APP_NAME}.app"
PKG_ID="com.winra.app"
PKG_VERSION="1.0.0"
INSTALLER_DIR="$SCRIPT_DIR/installer"
RESOURCES_DIR="$INSTALLER_DIR/resources"
PKG_BUILD_DIR="$SCRIPT_DIR/pkg_build"

echo "=== WinRA PKG Installer Build ==="
echo ""

# Check that .app exists
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: ${APP_PATH} tidak ditemukan."
    echo "Jalankan build.sh terlebih dahulu untuk membuat .app"
    exit 1
fi

echo "1/4 - Cleaning previous PKG build..."
rm -rf "$PKG_BUILD_DIR"
rm -f "${APP_NAME}.pkg"
rm -f "${APP_NAME}-component.pkg"

echo "2/4 - Creating component package..."
# Create a payload root with the .app in /Applications
mkdir -p "$PKG_BUILD_DIR/payload/Applications"
cp -R "$APP_PATH" "$PKG_BUILD_DIR/payload/Applications/"

# Strip extended attributes and re-sign
xattr -cr "$PKG_BUILD_DIR/payload/Applications/${APP_NAME}.app"
codesign -s - --force --all-architectures --timestamp --deep \
    "$PKG_BUILD_DIR/payload/Applications/${APP_NAME}.app" 2>/dev/null || true

# Build the component package
pkgbuild \
    --root "$PKG_BUILD_DIR/payload" \
    --identifier "$PKG_ID" \
    --version "$PKG_VERSION" \
    --install-location "/" \
    "$PKG_BUILD_DIR/WinRA-component.pkg"

echo "3/4 - Creating product installer..."
# Build the final product package with welcome/license/conclusion
productbuild \
    --distribution "$INSTALLER_DIR/distribution.xml" \
    --resources "$RESOURCES_DIR" \
    --package-path "$PKG_BUILD_DIR" \
    "${APP_NAME}.pkg"

echo "4/4 - Cleaning up..."
rm -rf "$PKG_BUILD_DIR"

echo ""
echo "=== PKG Build Complete ==="
PKG_SIZE=$(du -h "${APP_NAME}.pkg" | cut -f1)
echo "  Installer: ${APP_NAME}.pkg (${PKG_SIZE})"
echo ""
echo "Untuk install: open ${APP_NAME}.pkg"
echo "Atau double-click file ${APP_NAME}.pkg di Finder"
