#!/bin/bash

set -eux -o pipefail

PROJECT=qtox

tar -C /opt -zxf <(curl -L https://github.com/TokTok/dockerfiles/releases/download/nightly/qtox-wasm-buildhome.tar.gz)

. '/opt/buildhome/emsdk/emsdk_env.sh'
export PKG_CONFIG_PATH='/opt/buildhome/lib/pkgconfig'

emcmake cmake \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_FIND_ROOT_PATH='/opt/buildhome;/opt/buildhome/qt' \
  -B_build-wasm \
  -H.

cmake --build _build-wasm --parallel "$(nproc)"

mkdir _site

cp \
  platform/wasm/_headers \
  _build-wasm/qtloader.js \
  _build-wasm/qtlogo.svg \
  "_build-wasm/$PROJECT.js" \
  "_build-wasm/$PROJECT.wasm" \
  _site
cp "_build-wasm/$PROJECT.html" \
  _site/index.html
