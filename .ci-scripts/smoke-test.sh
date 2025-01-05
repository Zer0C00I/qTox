#!/bin/bash

set -eux -o pipefail

# Release tags *or* master builds where the current commit is tagged
# with 'v.*' are considered stable.
if [ -n "$(echo "$GITHUB_REF" | grep -o 'refs/tags/v.*')" ] ||
  [ -n "$(git tag --points-at HEAD | grep '^v.*')" ]; then
  REGEX="qTox v.* (stable)"
else
  REGEX="qTox v.* (unstable)"
fi

VERSION=$(curl \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  -L \
  https://api.github.com/repos/TokTok/qTox/releases/latest |
  grep '"tag_name": "v.*"' |
  grep -o 'v[^"]*')

"$@" --version | grep "$REGEX" || ("$@" --version && false)
"$@" --update-check | grep "^Latest version: $VERSION" || ("$@" --update-check && false)
