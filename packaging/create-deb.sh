#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2026 by The qTox Project Contributors

# Creates a DEB package from a pre-built AppDir produced by linuxdeploy.
# The AppDir already has all dependencies bundled and RPATH patched —
# this script just repackages it for Debian/Ubuntu.
# Only glibc and libstdc++ are left as system dependencies.

set -euo pipefail

usage() {
    echo "Usage: $0 --appdir DIR --src-dir DIR --out-dir DIR"
    echo "  --appdir   linuxdeploy AppDir/usr directory (pre-built, deps already bundled)"
    echo "  --src-dir  qTox source directory (for version info)"
    echo "  --out-dir  Directory to write the .deb file into"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --appdir)  APPDIR="$2";  shift 2 ;;
        --src-dir) SRC_DIR="$2"; shift 2 ;;
        --out-dir) OUT_DIR="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown argument: $1"; usage; exit 1 ;;
    esac
done

: "${APPDIR:?--appdir is required}"
: "${SRC_DIR:?--src-dir is required}"
: "${OUT_DIR:?--out-dir is required}"

VERSION=$(grep -m1 'VERSION_MAJOR' "$SRC_DIR/cmake/Package.cmake" | grep -oE '[0-9]+')
VERSION+=.$(grep -m1 'VERSION_MINOR' "$SRC_DIR/cmake/Package.cmake" | grep -oE '[0-9]+')
VERSION+=.$(grep -m1 'VERSION_PATCH' "$SRC_DIR/cmake/Package.cmake" | grep -oE '[0-9]+')
ARCH=$(dpkg --print-architecture)

STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT

echo "==> Installing AppDir to /opt/qtox"
# AppDir/usr/ becomes /opt/qtox/ — the RPATH ($ORIGIN/../lib) is already correct
# since the binary at bin/qtox-bin will still be one level above lib/.
mkdir -p "$STAGING/opt/qtox"
cp -a "$APPDIR/." "$STAGING/opt/qtox/"

echo "==> Creating launcher wrapper"
# Rename binary so the wrapper script can sit at the well-known path
mv "$STAGING/opt/qtox/bin/qtox" "$STAGING/opt/qtox/bin/qtox-bin"
cat > "$STAGING/opt/qtox/bin/qtox" << 'WRAPPER'
#!/bin/sh
exec /opt/qtox/bin/qtox-bin "$@"
WRAPPER
chmod 755 "$STAGING/opt/qtox/bin/qtox"

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
