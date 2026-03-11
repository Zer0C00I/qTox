#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2026 by The qTox Project Contributors

# Creates an RPM package that installs qTox into /opt/qtox/ and bundles
# all non-system libraries so the package works across Fedora releases.
# Only glibc and libstdc++ are left as system dependencies.

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

echo "==> Bundling shared libraries (recursive)"
mkdir -p "$STAGING/opt/qtox/lib"

# Iterative BFS: collect ALL transitive shared-library deps.
# Excluded: glibc family, C++ runtime, GPU drivers, display-server libs.
bundle_deps() {
    local outdir="$1"; shift
    # Exclude: kernel/glibc, C++ runtime, GPU drivers, display-server,
    #          audio-system daemons, and other system-ABI interfaces.
    local SKIP='linux-vdso|ld-linux'
    SKIP+='|libstdc\+\+\.so|libgcc_s\.so|libgomp\.so|libmvec\.so'
    SKIP+='|libc\.so\b|libm\.so\b|libdl\.so\b|libpthread\.so\b|librt\.so\b|libresolv\.so|libnss_'
    SKIP+='|libGL\.so\b|libGLX\.so|libGLdispatch\.so|libEGL\.so\b|libOpenGL\.so\b'
    SKIP+='|libdrm\.so|libOpenCL\.so|libvulkan\.so|libva\.so\b|libva-drm|libva-x11|libvdpau\.so'
    SKIP+='|libglslang|libSPIRV|libshaderc'
    SKIP+='|libX11\.so\b|libX11-xcb|libxcb|libXau\.so|libXdmcp\.so'
    SKIP+='|libXss\.so|libXext\.so|libXfixes\.so|libXrender\.so|libXv\.so'
    SKIP+='|libxkbcommon\.so'
    SKIP+='|libasound\.so|libpulse|libpipewire|libjack|libsndio\.so'
    SKIP+='|libdbus|libsystemd\.so|libudev\.so|libseccomp\.so'
    declare -A seen
    local queue=("$@")
    while [[ ${#queue[@]} -gt 0 ]]; do
        local cur="${queue[0]}"
        queue=("${queue[@]:1}")
        while IFS= read -r so; do
            [[ -z "$so" ]] && continue
            local base; base=$(basename "$so")
            [[ -n "${seen[$base]:-}" ]] && continue
            seen["$base"]=1
            cp -Lf "$so" "$outdir/"
            echo "  bundled: $base"
            queue+=("$so")
        done < <(ldd "$cur" 2>/dev/null | grep -oP '/[^\s]+' | grep -Pv "$SKIP")
    done
}

bundle_deps "$STAGING/opt/qtox/lib" "$BINARY"

echo "==> Bundling Qt6 plugins"
QT_PLUGIN_DIR=$(qmake6 -query QT_INSTALL_PLUGINS 2>/dev/null || \
                find /usr/lib64 /usr/lib -maxdepth 4 -name 'libqxcb.so' 2>/dev/null | \
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
    # Bundle transitive deps of the plugins too
    # shellcheck disable=SC2046
    bundle_deps "$STAGING/opt/qtox/lib" \
        $(find "$STAGING/opt/qtox/lib/qt6/plugins" -name '*.so' 2>/dev/null)
fi

echo "==> Patching RPATH (linuxdeploy-style: $ORIGIN-relative)"
# Patch the main binary to find bundled libs via RPATH so LD_LIBRARY_PATH
# is not required (same technique as linuxdeploy / AppImage).
patchelf --set-rpath '$ORIGIN/../lib' "$BINARY"
# Patch all bundled libs so they find each other
find "$STAGING/opt/qtox/lib" -maxdepth 1 -name '*.so*' -type f | while read -r lib; do
    patchelf --set-rpath '$ORIGIN' "$lib" 2>/dev/null || true
done
# Patch Qt plugins: they live two levels deep (lib/qt6/plugins/<subdir>/*.so)
find "$STAGING/opt/qtox/lib/qt6/plugins" -name '*.so' -type f | while read -r plugin; do
    patchelf --set-rpath '$ORIGIN/../../../' "$plugin" 2>/dev/null || true
done

echo "==> Creating launcher wrapper"
mv "$BINARY" "$STAGING/opt/qtox/bin/qtox-bin"
# qt.conf tells Qt where to find bundled plugins (RPATH alone doesn't cover plugins)
mkdir -p "$STAGING/opt/qtox/bin"
cat > "$STAGING/opt/qtox/bin/qt.conf" << 'QTCONF'
[Paths]
Plugins = ../lib/qt6/plugins
QTCONF
cat > "$BINARY" << 'WRAPPER'
#!/bin/sh
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
