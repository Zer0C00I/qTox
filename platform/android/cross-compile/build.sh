#!/bin/bash

# Usage: ./build.sh --arch [armv7a|arm64-v8a|x86|x86_64] --build-type [Debug|Release]

set -eu

while (($# > 0)); do
  case $1 in
    --arch)
      ARCH="$2"
      shift 2
      ;;
    --build-type)
      BUILD_TYPE="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "Unexpected argument $1"
      exit 1
      ;;
  esac
done

echo "Building $BUILD_TYPE build for $ARCH"

export QT_ANDROID_KEYSTORE_PATH="$PWD/platform/android/keystore.jks"
export QT_ANDROID_KEYSTORE_ALIAS=mydomain
export QT_ANDROID_KEYSTORE_STORE_PASS=aoeuaoeu
export QT_ANDROID_KEYSTORE_KEY_PASS=aoeuaoeu

/opt/buildhome/android/qt/bin/qt-cmake \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache \
  -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
  -DQT_ANDROID_SIGN_APK=ON \
  -GNinja \
  -B_build \
  -H. \
  "$@"

cmake --build _build --target apk
