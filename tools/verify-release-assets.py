#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024-2025 The TokTok team
import argparse
import multiprocessing
import os
import subprocess  # nosec
import sys
import tempfile
from dataclasses import dataclass
from typing import Any

import requests
from lib import git
from lib import github

NEEDS_SIGNATURE = (".apk", ".dmg", ".exe", ".flatpak", ".gz", ".xz")


@dataclass
class Config:
    tag: str


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="""
    Download binaries and signatures from the GitHub release and verify the
    signatures.
    """)
    parser.add_argument(
        "--tag",
        help="Tag to create signatures for",
        default=git.current_tag(),
    )
    return Config(**vars(parser.parse_args()))


def verify_signature(tmpdir: str, binary: str) -> None:
    subprocess.run(  # nosec
        [
            "gpg",
            "--verify",
            os.path.join(tmpdir, f"{binary}.asc"),
            os.path.join(tmpdir, binary),
        ],
        check=True,
    )


def download_and_verify(
        args: tuple[str, dict[str, Any], dict[str, Any]]) -> None:
    tmpdir, asset, by_name = args
    binary = asset["name"]
    print(f"Downloading {binary} and {binary}.asc", file=sys.stderr)
    with open(os.path.join(tmpdir, binary), "wb") as f:
        f.write(requests.get(asset["browser_download_url"]).content)
    with open(os.path.join(tmpdir, f"{binary}.asc"), "wb") as f:
        f.write(
            requests.get(
                by_name[f"{binary}.asc"]["browser_download_url"]).content)
    verify_signature(tmpdir, binary)


def download_and_verify_binaries(config: Config, tmpdir: str) -> None:
    response = requests.get(
        f"https://api.github.com/repos/TokTok/qTox/releases/tags/{config.tag}",
        headers=github.auth_headers(required=False),
    )
    response.raise_for_status()
    assets = response.json()["assets"]
    by_name = {asset["name"]: asset for asset in assets}
    todo = [
        asset for asset in assets if asset["name"].endswith(NEEDS_SIGNATURE)
    ]
    with multiprocessing.Pool() as pool:
        pool.map(download_and_verify,
                 [(tmpdir, asset, by_name) for asset in todo])


def main(config: Config) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        download_and_verify_binaries(config, tmpdir)


if __name__ == "__main__":
    main(parse_args())
