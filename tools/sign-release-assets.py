#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 The TokTok team
import argparse
import os
import subprocess  # nosec
import tempfile
from dataclasses import dataclass
from functools import cache as memoize

import requests

BINARY_EXTENSIONS = (".apk", ".dmg", ".exe", ".flatpak")


@dataclass
class Config:
    upload: bool
    tag: str


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="""
    Download the binaries from the GitHub release, sign them, and upload
    the signatures to the GitHub release.
    """)
    parser.add_argument(
        "--upload",
        action=argparse.BooleanOptionalAction,
        help="Upload signatures to GitHub (disabling this is a dryrun)",
        default=True,
    )
    parser.add_argument(
        "--tag",
        help="Tag to create signatures for",
        default=git_tag(),
    )
    return Config(**vars(parser.parse_args()))


@memoize
def github_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN is needed to upload tarballs")
    return token


@memoize
def github_release_id(tag: str) -> str:
    response = requests.get(
        f"https://api.github.com/repos/TokTok/qTox/releases/tags/{tag}",
        headers={
            "Authorization": f"token {github_token()}",
        },
    )
    response.raise_for_status()
    return str(response.json()["id"])


def git_tag() -> str:
    return (subprocess.check_output(  # nosec
        [
            "git",
            "describe",
            "--tags",
            "--abbrev=0",
            "--match",
            "v*",
        ]).decode("utf-8").strip())


def needs_signing(name: str, asset_names: list[str]) -> bool:
    return (os.path.splitext(name)[1] in BINARY_EXTENSIONS
            and name + ".asc" not in asset_names)


def sign_binary(binary: str, tmpdir: str) -> None:
    print(f"Signing {binary}")
    subprocess.run(  # nosec
        [
            "gpg",
            "--armor",
            "--detach-sign",
            os.path.join(tmpdir, binary),
        ],
        check=True,
    )


def upload_signature(tag: str, tmpdir: str, binary: str) -> None:
    release_id = github_release_id(tag)
    print(f"Uploading signature for {binary}")
    with open(os.path.join(tmpdir, f"{binary}.asc"), "rb") as f:
        response = requests.post(
            f"https://uploads.github.com/repos/TokTok/qTox/releases/{release_id}/assets?name={binary}.asc",
            headers={
                "Authorization": f"token {github_token()}",
                "Content-Type": "application/pgp-signature",
            },
            data=f,
        )
        response.raise_for_status()


def download_and_sign_binaries(config: Config, tmpdir: str) -> None:
    response = requests.get(
        f"https://api.github.com/repos/TokTok/qTox/releases/tags/{config.tag}",
        headers={
            "Authorization": f"token {github_token()}",
        },
    )
    response.raise_for_status()
    assets = response.json()["assets"]
    asset_names = [asset["name"] for asset in assets]
    for asset in assets:
        binary = asset["name"]
        if needs_signing(binary, asset_names):
            with open(os.path.join(tmpdir, binary), "wb") as f:
                print(f"Downloading {binary}")
                f.write(requests.get(asset["browser_download_url"]).content)
            sign_binary(binary, tmpdir)
            if config.upload:
                upload_signature(config.tag, tmpdir, binary)


def main(config: Config) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        download_and_sign_binaries(config, tmpdir)


if __name__ == "__main__":
    main(parse_args())
