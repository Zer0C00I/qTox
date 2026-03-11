#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2026 by The qTox Project Contributors

# Creates an RPM package from a pre-built AppDir produced by linuxdeploy.
# The AppDir already has all dependencies bundled and RPATH patched —
# this script just repackages it for Fedora/RHEL.
# Only glibc and libstdc++ are left as system dependencies.

set -euo pipefail

usage() {
    echo "Usage: $0 --appdir DIR --src-dir DIR --out-dir DIR"
    echo "  --appdir   linuxdeploy AppDir/usr directory (pre-built, deps already bundled)"
    echo "  --src-dir  qTox source directory (for version info)"
    echo "  --out-dir  Directory to write the .rpm file into"
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
DIST=$(rpm --eval '%{?dist}' 2>/dev/null || echo ".fc41")
ARCH=$(uname -m)

STAGING=$(mktemp -d)
RPMBUILD="$HOME/rpmbuild"
trap 'rm -rf "$STAGING"' EXIT

echo "==> Installing AppDir to /opt/qtox"
# AppDir/usr/ becomes /opt/qtox/ — the RPATH ($ORIGIN/../lib) is already correct.
mkdir -p "$STAGING/opt/qtox"
cp -a "$APPDIR/." "$STAGING/opt/qtox/"

echo "==> Creating launcher wrapper"
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

# All dependencies except glibc and libstdc++ are bundled in /opt/qtox/lib/.
AutoReqProv: no
Requires: glibc >= 2.35
Requires: libstdc++

%description
qTox is an instant messaging client using the encrypted peer-to-peer
Tox protocol. Supports text chat, file transfers, audio/video calls
and conferences.

All dependencies except glibc and libstdc++ are bundled in /opt/qtox/lib/.

%install
cp -a "${BUILDROOT}/.." %{buildroot}/

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
- Bundled all dependencies for cross-release compatibility
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
