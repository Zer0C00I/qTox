#!/bin/bash

source "/work/emsdk/emsdk_env.sh"

export PKG_CONFIG_PATH="/work/lib/pkgconfig"

emcmake cmake \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DCMAKE_FIND_ROOT_PATH="/work;/work/qt" \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DSTRICT_OPTIONS=ON \
  -DBUILD_TESTING=OFF \
  -GNinja \
  -B_build-wasm \
  -H.

cmake --build _build-wasm
