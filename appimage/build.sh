#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2019 by The qTox Project Contributors
# Copyright © 2024-2025 The TokTok team

# Fail out on error
set -exuo pipefail

usage() {
  echo "$0 --src-dir SRC_DIR"
  echo "Builds an app image in the CWD based off qtox installation at SRC_DIR"
}

while (($# > 0)); do
  case $1 in
    --src-dir)
      QTOX_SRC_DIR=$2
      shift 2
      ;;
    --help | -h)
      usage
      exit 1
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

# directory paths
BUILD_DIR=$(realpath .)
readonly BUILD_DIR
QTOX_APP_DIR="$BUILD_DIR/QTox.AppDir"
readonly QTOX_APP_DIR

rm -f appimagetool-*.AppImage
wget "https://github.com/$(wget -q https://github.com/probonopd/go-appimage/releases/expanded_assets/continuous -O - | grep "appimagetool-.*-x86_64.AppImage" | head -n 1 | cut -d '"' -f 2)"
chmod +x appimagetool-*.AppImage

# update information to be embeded in AppImage
#readonly UPDATE_INFO="gh-releases-zsync|TokTok|qTox|latest|qTox-*.x86_64.AppImage.zsync"
#export GIT_VERSION=$(git -C "${QTOX_SRC_DIR}" rev-parse --short HEAD)

echo "$QTOX_APP_DIR"
cmake "$QTOX_SRC_DIR" \
  -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="/work/lib64/cmake;/work/qt/lib/cmake" \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DUPDATE_CHECK=ON \
  -B _build
cmake --build _build
#rm -fr QTox.AppDir
cmake --install _build --prefix QTox.AppDir/usr

export QTDIR=/work/qt
export LD_LIBRARY_PATH="/work/lib64:$QTDIR/lib"

./appimagetool-*.AppImage --appimage-extract-and-run -s deploy "$QTOX_APP_DIR"/usr/share/applications/*.desktop

# print all links not contained inside the AppDir
LD_LIBRARY_PATH='' find "$QTOX_APP_DIR" -type f -exec ldd {} \; 2>&1 | grep '=>' | grep -v "$QTOX_APP_DIR"

./appimagetool-*.AppImage --appimage-extract-and-run "$QTOX_APP_DIR"
