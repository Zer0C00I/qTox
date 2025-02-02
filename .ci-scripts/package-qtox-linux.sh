#!/bin/bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2021 by The qTox Project Contributors
# Copyright © 2024-2025 The TokTok team

set -euo pipefail

usage() {
  echo "Usage: $0 [--source-dir] [--target-dir]"
  echo "Build qTox and generate rpm package."
}

if [ $# -lt 4 ]; then
  usage
  exit 1
fi

while (($# > 0)); do
  case $1 in
    --source-dir)
      SRCDIR="$2"
      shift 2
      ;;
    --target-dir)
      BUILD_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unexpected argument $1"
      usage
      exit 1
      ;;
  esac
done

if [ ! -d "$SRCDIR" ]; then
  echo "The source directory \"$SRCDIR\" does not exists."
  usage
  exit 1
fi

dnf install rpmbuild -y
mkdir -p "$BUILD_DIR"
# Check that the rpm file was created.
cmake "$SRCDIR" -B"$BUILD_DIR"
cmake --build "$BUILD_DIR" -- package
# We add echo "" not to avoid failing on the line below if the folder does not have RPM package, we will fail gracefully afterwards.
rpm_file="$(ls "$BUILD_DIR" | grep -E "qtox-[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?-fc[0-9]+\.x86_64\.rpm" || echo "")"
if [ -z "$rpm_file" ]; then
  echo "Error! The rpm package was not build!"
  exit 1
else
  echo "$rpm_file was successfully generated."
  echo "$(ls -lh "$BUILD_DIR/$rpm_file")"
fi
exit 0
