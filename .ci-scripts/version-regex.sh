#!/bin/bash

set -eux -o pipefail

# Release tags *or* master builds where the current commit is tagged
# with 'v.*' are considered stable.
if [ -n "$(echo "$GITHUB_REF" | grep -o 'refs/tags/v.*')" ] || [ -n "$(git tag --points-at HEAD | grep '^v.*')" ]; then
  echo "regex=qTox v.* (stable)" >>"$GITHUB_OUTPUT"
else
  echo "regex=qTox v.* (unstable)" >>"$GITHUB_OUTPUT"
fi
