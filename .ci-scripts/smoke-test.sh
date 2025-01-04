#!/bin/bash

set -eux -o pipefail

# Release tags *or* master builds where the current commit is tagged
# with 'v.*' are considered stable. We also consider the version stable
# if the current commit message is "chore: Release v.*".
if [ -n "$(echo "$GITHUB_REF" | grep -o 'refs/tags/v.*')" ] ||
  [ -n "$(git tag --points-at HEAD | grep '^v.*')" ] ||
  [ -n "$(git log -1 --pretty=%B | grep '^chore: Release v.*')" ]; then
  REGEX="qTox v.* (stable)"
else
  REGEX="qTox v.* (unstable)"
fi

"$@" --version | grep "$REGEX" || ("$@" --version && false)
"$@" --update-check
