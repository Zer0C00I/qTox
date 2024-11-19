#!/bin/bash

#    Copyright © 2022 by The qTox Project Contributors
#
#    This program is libre software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

set -euo pipefail

readonly SCRIPT_DIR="$(dirname "$(realpath "$0")")"
if [ ! -d "$SCRIPT_DIR/dockerfiles" ]; then
  git clone --depth=1 https://github.com/TokTok/dockerfiles "$SCRIPT_DIR/dockerfiles"
fi

install_deps() {
  for dep in "$@"; do
    mkdir -p _build-dep
    pushd _build-dep
    "$SCRIPT_DIR/dockerfiles/qtox/$dep" --arch macos
    popd
    rm -rf _build-dep
  done
}

install_deps \
    build_openssl.sh \
    build_qrencode.sh \
    build_libexif.sh \
    build_sodium.sh \
    build_openal.sh \
    build_vpx.sh \
    build_opus.sh \
    build_ffmpeg.sh \
    build_toxcore.sh \
    build_sqlcipher.sh \
