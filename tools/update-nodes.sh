#!/bin/bash

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2020 by The qTox Project Contributors
# Copyright © 2024-2025 The TokTok team

# script to update the list of bootstrap nodes
#
# it should be run before releasing a new version
##
# requires:
#  * curl
#  * python3

# usage:
#
#   ./$script

set -eu -o pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly NODES_FILE="$SCRIPT_DIR/../res/nodes.json"
readonly NODES_URL="https://nodes.tox.chat/json"

curl "$NODES_URL" | python3 -c '
import json
import sys
print(json.dumps(json.loads(sys.stdin.read()), indent=2))
' >"$NODES_FILE.new"
mv "$NODES_FILE.new" "$NODES_FILE"
