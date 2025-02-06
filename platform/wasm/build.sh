#!/bin/bash

source "/opt/buildhome/emsdk/emsdk_env.sh"

export PKG_CONFIG_PATH="/opt/buildhome/lib/pkgconfig"

emcmake cmake \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DCMAKE_FIND_ROOT_PATH="/opt/buildhome;/opt/buildhome/qt" \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DSTRICT_OPTIONS=ON \
  -DBUILD_TESTING=OFF \
  -GNinja \
  -B_build-wasm \
  -H.

cmake --build _build-wasm
