#!/bin/bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2022 by The qTox Project Contributors
# Copyright © 2024 The TokTok team

set -euo pipefail

readonly SCRIPT_DIR="$(dirname "$(realpath "$0")")"
. "$SCRIPT_DIR/macos_install_deps.sh"

install_deps \
  build_openssl.sh \
  build_qrencode.sh \
  build_libexif.sh \
  build_sodium.sh \
  build_openal.sh \
  build_vpx.sh \
  build_opus.sh \
  build_ffmpeg.sh \
  build_sqlcipher.sh \
  build_hunspell.sh \
  build_extra_cmake_modules.sh \
  build_sonnet.sh \
  build_toxcore.sh
