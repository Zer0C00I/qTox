# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 The TokTok team
import re


def parse() -> dict[str, str]:
    messages: dict[str, str] = {}

    with open("CHANGELOG.md", "r") as f:
        version = None
        message: list[str] = []
        for line in f.read().splitlines():
            version_found = re.search(r"^##\s*(v[^ ]+)", line)
            if version_found:
                version = version_found.group(1)
                continue
            if version:
                if line.startswith("####") or line.startswith("<a name="):
                    while message and not message[-1].strip():
                        message.pop()
                    while message and not message[0].strip():
                        message.pop(0)
                    messages[version] = "\n".join(message)
                    version = None
                    message = []
                else:
                    message.append(line)

    return messages


def get_message(version: str) -> str:
    messages = parse()
    return messages[version]
