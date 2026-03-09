#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2026 by The qTox Project Contributors

# Creates a DEB package that installs qTox into /opt/qtox/ and bundles
# all non-system libraries so the package works across distros.
# Only glibc and libstdc++ are left as system dependencies.

set -euo pipefail

usage() {
    echo "Usage: $0 --build-dir DIR --src-dir DIR --out-dir DIR"
    echo "  --build-dir  CMake build directory containing the qtox binary"
    echo "  --src-dir    qTox source directory"
    echo "  --out-dir    Directory to write the .deb file into"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-dir) BUILD_DIR="$2"; shift 2 ;;
        --src-dir)   SRC_DIR="$2";   shift 2 ;;
        --out-dir)   OUT_DIR="$2";   shift 2 ;;
        -h|--help)   usage; exit 0 ;;
        *) echo "Unknown argument: $1"; usage; exit 1 ;;
    esac
done

: "${BUILD_DIR:?--build-dir is required}"
: "${SRC_DIR:?--src-dir is required}"
: "${OUT_DIR:?--out-dir is required}"

VERSION=$(grep -m1 'VERSION_MAJOR' "$SRC_DIR/cmake/Package.cmake" | grep -oE '[0-9]+')
VERSION+=.$(grep -m1 'VERSION_MINOR' "$SRC_DIR/cmake/Package.cmake" | grep -oE '[0-9]+')
VERSION+=.$(grep -m1 'VERSION_PATCH' "$SRC_DIR/cmake/Package.cmake" | grep -oE '[0-9]+')
ARCH=$(dpkg --print-architecture)

STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT

echo "==> Installing qTox to /opt/qtox"
cmake --install "$BUILD_DIR" --prefix "$STAGING/opt/qtox"

BINARY="$STAGING/opt/qtox/bin/qtox"

echo "==> Bundling shared libraries"
mkdir -p "$STAGING/opt/qtox/lib"

for lib in \
    libavcodec libavformat libavutil libavdevice libswscale \
    libvpx libsqlcipher libtoxcore \
    libopenal libopus libsodium \
    libexif libqrencode libunwind \
    libQt6Core libQt6Gui libQt6Widgets libQt6Network \
    libQt6Svg libQt6Xml libQt6DBus libQt6OpenGL; do
    so=$(ldd "$BINARY" | grep -o '/[^ ]*'"$lib"'[^ ]*' | head -1 || true)
    if [[ -n "$so" ]]; then
        cp -L "$so" "$STAGING/opt/qtox/lib/"
        echo "  bundled: $(basename "$so")"
    fi
done

echo "==> Bundling Qt6 plugins"
QT_PLUGIN_DIR=$(qmake6 -query QT_INSTALL_PLUGINS 2>/dev/null || \
                find /usr/lib -maxdepth 4 -name 'libqxcb.so' 2>/dev/null | \
                head -1 | xargs -r dirname || true)

if [[ -n "$QT_PLUGIN_DIR" && -d "$QT_PLUGIN_DIR" ]]; then
    for plugin_subdir in platforms imageformats iconengines; do
        src="$QT_PLUGIN_DIR/$plugin_subdir"
        if [[ -d "$src" ]]; then
            dst="$STAGING/opt/qtox/lib/qt6/plugins/$plugin_subdir"
            mkdir -p "$dst"
            cp "$src/"*.so "$dst/" 2>/dev/null || true
            echo "  plugins: $plugin_subdir"
        fi
    done
fi

echo "==> Creating launcher wrapper"
mv "$BINARY" "$STAGING/opt/qtox/bin/qtox-bin"
cat > "$BINARY" << 'WRAPPER'
#!/bin/sh
export LD_LIBRARY_PATH=/opt/qtox/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export QT_PLUGIN_PATH=/opt/qtox/lib/qt6/plugins
exec /opt/qtox/bin/qtox-bin "$@"
WRAPPER
chmod 755 "$BINARY"

echo "==> Installing desktop integration to /usr/share"
mkdir -p "$STAGING/usr/share/applications"
mkdir -p "$STAGING/usr/share/metainfo"

cp "$STAGING/opt/qtox/share/applications/"*.desktop \
   "$STAGING/usr/share/applications/" 2>/dev/null || true
cp "$STAGING/opt/qtox/share/metainfo/"*.xml \
   "$STAGING/usr/share/metainfo/"       2>/dev/null || true

for size in 14 16 22 24 32 36 48 64 72 96 128 192 256 512; do
    src="$STAGING/opt/qtox/share/icons/hicolor/${size}x${size}"
    if [[ -d "$src" ]]; then
        dst="$STAGING/usr/share/icons/hicolor/${size}x${size}"
        mkdir -p "$dst"
        cp -r "$src/." "$dst/"
    fi
done

echo "==> Creating DEBIAN control files"
mkdir -p "$STAGING/DEBIAN"

cat > "$STAGING/DEBIAN/postinst" << 'SCRIPT'
#!/bin/sh
set -e
ln -sf /opt/qtox/bin/qtox /usr/bin/qtox
if command -v update-icon-caches > /dev/null 2>&1; then
    update-icon-caches /usr/share/icons/hicolor || true
fi
SCRIPT
chmod 755 "$STAGING/DEBIAN/postinst"

cat > "$STAGING/DEBIAN/postrm" << 'SCRIPT'
#!/bin/sh
set -e
rm -f /usr/bin/qtox
SCRIPT
chmod 755 "$STAGING/DEBIAN/postrm"

cat > "$STAGING/DEBIAN/control" << EOF
Package: qtox
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: qTox contributors <noreply@github.com>
Section: net
Priority: optional
Description: Tox-based encrypted instant messenger
 qTox is an instant messaging client using the encrypted peer-to-peer
 Tox protocol. Supports text chat, file transfers, audio/video calls
 and conferences.
 .
 All dependencies except glibc and libstdc++ are bundled in /opt/qtox/lib/.
Depends: libc6 (>= 2.35),
 libstdc++6
EOF

mkdir -p "$OUT_DIR"
echo "==> Building DEB package"
dpkg-deb --build --root-owner-group "$STAGING" "$OUT_DIR/qtox-${VERSION}-${ARCH}.deb"
echo "Created: $OUT_DIR/qtox-${VERSION}-${ARCH}.deb"
