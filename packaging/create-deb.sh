#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2026 by The qTox Project Contributors

# Creates a DEB package that installs qTox into /opt/qtox/ and bundles
# FFmpeg and libvpx alongside the binary so the package works across
# Ubuntu 22.04, Ubuntu 24.04, Debian 12, Debian 13, etc.

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

echo "==> Bundling FFmpeg and libvpx"
mkdir -p "$STAGING/opt/qtox/lib"

for lib in libavcodec libavformat libavutil libavdevice libswscale libvpx; do
    so=$(ldd "$BINARY" | grep -o '/[^ ]*'"$lib"'[^ ]*' | head -1 || true)
    if [[ -n "$so" ]]; then
        cp -L "$so" "$STAGING/opt/qtox/lib/"
        echo "  bundled: $(basename "$so")"
    fi
done

echo "==> Setting RPATH to \$ORIGIN/../lib"
patchelf --set-rpath '$ORIGIN/../lib' "$BINARY"

echo "==> Installing desktop integration to /usr/share"
# Desktop file, icons and appdata go to standard system paths so the app
# appears in application menus and file managers on any distro.
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
 FFmpeg and libvpx are bundled in /opt/qtox/lib/ for cross-distro
 compatibility.
Depends: libc6 (>= 2.35),
 libstdc++6,
 libqt6core6 | libqt6core6t64,
 libqt6gui6 | libqt6gui6t64,
 libqt6widgets6 | libqt6widgets6t64,
 libqt6network6 | libqt6network6t64,
 libqt6svg6 | libqt6svg6t64,
 libqt6xml6 | libqt6xml6t64,
 libqt6dbus6 | libqt6dbus6t64,
 libopenal1,
 libopus0,
 libsodium23,
 libsqlcipher0,
 libexif12,
 libqrencode4,
 libxss1,
 libunwind8
EOF

mkdir -p "$OUT_DIR"
echo "==> Building DEB package"
dpkg-deb --build --root-owner-group "$STAGING" "$OUT_DIR/qtox-${VERSION}-${ARCH}.deb"
echo "Created: $OUT_DIR/qtox-${VERSION}-${ARCH}.deb"
