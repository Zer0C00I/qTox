#!/bin/bash

set -eux -o pipefail

# Release tags *or* master builds where the current commit is tagged
# with 'v.*' are considered stable. We also consider the version stable
# if the current commit message is "chore: Release v.*".
if [ -n "$(echo "$GITHUB_REF" | grep -o 'refs/tags/v.*')" ] ||
  [ -n "$(git tag --points-at HEAD | grep '^v.*')" ] ||
  [ -n "$(git log -1 --pretty=%B | grep '^chore: Release v.*')" ]; then
  echo "regex=qTox v.* (stable)" >>"$GITHUB_OUTPUT"
else
  echo "regex=qTox v.* (unstable)" >>"$GITHUB_OUTPUT"
fi
