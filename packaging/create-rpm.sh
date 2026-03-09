#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2026 by The qTox Project Contributors

# Creates an RPM package that installs qTox into /opt/qtox/ and bundles
# FFmpeg and libvpx alongside the binary so the package works across
# Fedora releases regardless of the system FFmpeg version.

set -euo pipefail

usage() {
    echo "Usage: $0 --build-dir DIR --src-dir DIR --out-dir DIR"
    echo "  --build-dir  CMake build directory containing the qtox binary"
    echo "  --src-dir    qTox source directory"
    echo "  --out-dir    Directory to write the .rpm file into"
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
DIST=$(rpm --eval '%{?dist}' 2>/dev/null || echo ".fc41")
ARCH=$(uname -m)

STAGING=$(mktemp -d)
RPMBUILD="$HOME/rpmbuild"
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

echo "==> Creating RPM spec"
mkdir -p "$RPMBUILD"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

BUILDROOT="$RPMBUILD/BUILDROOT/qtox-${VERSION}-1${DIST}.${ARCH}"
mkdir -p "$BUILDROOT"
cp -a "$STAGING/." "$BUILDROOT/"

cat > "$RPMBUILD/SPECS/qtox.spec" << SPEC
Name:       qtox
Version:    ${VERSION}
Release:    1%{?dist}
Summary:    Tox-based encrypted instant messenger
License:    GPLv3+
URL:        https://github.com/Zer0C00I/qTox

# FFmpeg and libvpx are bundled in /opt/qtox/lib — exclude them from
# automatic dependency/provides scanning to avoid conflicts.
AutoReqProv: no
Requires: glibc >= 2.35
Requires: libstdc++
Requires: qt6-qtbase >= 6.2
Requires: qt6-qtsvg
Requires: openal-soft
Requires: opus
Requires: libsodium
Requires: sqlcipher
Requires: libexif
Requires: qrencode-libs
Requires: libXScrnSaver
Requires: libunwind

%description
qTox is an instant messaging client using the encrypted peer-to-peer
Tox protocol. Supports text chat, file transfers, audio/video calls
and conferences.

FFmpeg and libvpx are bundled in /opt/qtox/lib/ for compatibility
across Fedora releases.

%install
cp -a "${BUILDROOT}/." %{buildroot}/

%post
ln -sf /opt/qtox/bin/qtox /usr/bin/qtox
gtk-update-icon-cache /usr/share/icons/hicolor &>/dev/null || true

%postun
rm -f /usr/bin/qtox

%files
/opt/qtox/
/usr/share/applications/
/usr/share/metainfo/
/usr/share/icons/

%changelog
* $(date '+%a %b %d %Y') qTox contributors <noreply@github.com> - ${VERSION}-1
- Bundled FFmpeg and libvpx for cross-release compatibility
SPEC

echo "==> Building RPM"
rpmbuild -bb \
    --define "_topdir $RPMBUILD" \
    --define "_builddir $RPMBUILD/BUILD" \
    --define "_buildrootdir $RPMBUILD/BUILDROOT" \
    "$RPMBUILD/SPECS/qtox.spec"

mkdir -p "$OUT_DIR"
find "$RPMBUILD/RPMS" -name "qtox-*.rpm" -exec cp {} "$OUT_DIR/" \;
echo "Created: $(ls "$OUT_DIR"/qtox-*.rpm)"
