#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2019 by The qTox Project Contributors
# Copyright © 2024-2025 The TokTok team

# Fail out on error
set -exuo pipefail

usage() {
  echo "$0 --src-dir SRC_DIR"
  echo "Builds an AppImage in the CWD using linuxdeploy + linuxdeploy-plugin-qt."
  echo "Requires: cmake, ninja, clang++, Qt6, wget, toxcore installed."
}

while (($# > 0)); do
  case $1 in
    --src-dir)
      QTOX_SRC_DIR=$(realpath "$2")
      shift 2
      ;;
    --help | -h)
      usage
      exit 0
      ;;
    *)
      echo "Unexpected argument $1"
      usage
      exit 1
      ;;
  esac
done

if [ -z "${QTOX_SRC_DIR+x}" ]; then
  echo "--src-dir is a required argument"
  usage
  exit 1
fi

# Build qTox
cmake -GNinja -B _build_appimage -S "$QTOX_SRC_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DSTRICT_OPTIONS=ON \
  -DUPDATE_CHECK=ON \
  -DSPELL_CHECK=OFF
cmake --build _build_appimage --parallel "$(nproc)"
cmake --install _build_appimage --prefix AppDir/usr

# Download linuxdeploy and Qt plugin
wget -q https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
wget -q https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage linuxdeploy-plugin-qt-x86_64.AppImage

# Bundle into AppImage
APPIMAGE_EXTRACT_AND_RUN=1 \
QMAKE=/usr/bin/qmake6 \
  ./linuxdeploy-x86_64.AppImage \
    --appdir AppDir \
    --plugin qt \
    --desktop-file "$QTOX_SRC_DIR/platform/linux/io.github.qtox.qTox.desktop" \
    --icon-file "$QTOX_SRC_DIR/assets/img/icons/512x512/qtox.png" \
    --output appimage
