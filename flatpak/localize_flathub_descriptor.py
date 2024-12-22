#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2021 by The qTox Project Contributors
# Copyright © 2024 The TokTok team
import json
import subprocess  # nosec
import sys

QTOX_GIT_URL = "https://github.com/TokTok/qTox"


def commit_from_tag(url: str, tag: str) -> str:
    git_output = subprocess.run(  # nosec
        ["git", "ls-remote", url, f"{tag}^{{}}"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return git_output.stdout.split(b"\t")[0].decode()


def git_tag() -> str:
    git_output = subprocess.run(  # nosec
        ["git", "describe", "--tags", "--abbrev=0"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return git_output.stdout.decode().strip()


def localize_flathub_descriptor(flathub_descriptor_path: str,
                                output_path: str) -> None:
    with open(flathub_descriptor_path) as f:
        flathub_descriptor = json.load(f)

    # Update the flathub descriptor for qTox to point sources at /qtox/.
    for module in flathub_descriptor["modules"]:
        if module["name"] == "qTox":
            if module["sources"][0]["type"] == "git":
                module["sources"] = [{
                    "type": "dir",
                    "path": "/qtox/",
                }]
            else:
                tag = git_tag()
                commit = commit_from_tag(QTOX_GIT_URL, tag)
                # Reverse if we run the script twice.
                module["sources"] = [{
                    "type": "git",
                    "url": QTOX_GIT_URL,
                    "commit": commit,
                    "tag": tag,
                }]

    with open(output_path, "w") as f:
        json.dump(flathub_descriptor, f, indent=2)
        f.write("\n")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <flathub_descriptor_path> <output_path>")
        sys.exit(1)

    flathub_descriptor_path = sys.argv[1]
    output_path = sys.argv[2]
    localize_flathub_descriptor(flathub_descriptor_path, output_path)


if __name__ == "__main__":
    main()
