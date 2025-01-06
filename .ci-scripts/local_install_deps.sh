#!/bin/bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2022 by The qTox Project Contributors
# Copyright © 2024-2025 The TokTok team

set -euxo pipefail

if [ ! -d "$SCRIPT_DIR/dockerfiles" ]; then
  if [ -d "$SCRIPT_DIR/../../dockerfiles" ]; then
    ln -s "$SCRIPT_DIR/../../dockerfiles" "$SCRIPT_DIR/dockerfiles"
  else
    git clone --depth=1 https://github.com/TokTok/dockerfiles "$SCRIPT_DIR/dockerfiles"
  fi
fi

case "$(uname -s)" in
  Darwin)
    SYSTEM="macos"
    ;;
  Linux)
    SYSTEM="linux"
    ;;
  *)
    echo "Unsupported system: $(uname -s)"
    exit 1
    ;;
esac

ARCH="${1:-$(uname -m)}"
BUILD_TYPE="${2:-release}"
SANITIZE="${3:-}"

install_deps() {
  DEP_PREFIX="$SCRIPT_DIR/dockerfiles/local-deps"
  for dep in "$@"; do
    mkdir -p "external/$dep"
    pushd "external/$dep"
    if [ -f "$SCRIPT_DIR/dockerfiles/qtox/build_${dep}_$SYSTEM.sh" ]; then
      SCRIPT="$SCRIPT_DIR/dockerfiles/qtox/build_${dep}_$SYSTEM.sh"
    else
      SCRIPT="$SCRIPT_DIR/dockerfiles/qtox/build_$dep.sh"
    fi
    "$SCRIPT" --arch "$SYSTEM-$ARCH" --libtype "static" --buildtype "$BUILD_TYPE" --sanitize "$SANITIZE" --prefix "$DEP_PREFIX"
    popd
    rm -rf "external/$dep"
  done
  rmdir external
}
