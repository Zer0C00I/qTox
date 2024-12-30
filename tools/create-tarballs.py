#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 The TokTok team
import argparse
import os
import subprocess  # nosec
import tempfile
from dataclasses import dataclass

import requests
from lib import git
from lib import github


@dataclass
class Config:
    upload: bool
    tag: str


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="""
    Create and optionally upload source tarballs for the project.
    """)
    parser.add_argument(
        "--upload",
        action=argparse.BooleanOptionalAction,
        help="Upload tarballs to GitHub",
        default=False,
    )
    parser.add_argument(
        "--tag",
        help="Tag to create tarballs for",
        default=git.current_tag(),
    )
    return Config(**vars(parser.parse_args()))


def create_tarballs(tag: str, tmpdir: str) -> None:
    """Create source tarballs with both .gz and .xz for the given tag."""
    for prog in ("gzip", "xz"):
        tarname = f"{os.path.join(tmpdir, tag)}.tar"
        print(f"Creating {prog} tarball for {tag}")
        subprocess.run(  # nosec
            [
                "git",
                "archive",
                "--format=tar",
                "--prefix=qTox-{tag}/",
                tag,
                f"--output={tarname}",
            ],
            check=True,
        )
        subprocess.run([prog, "-f", tarname], check=True)  # nosec


def sign_tarballs(tag: str, tmpdir: str) -> None:
    """Sign the tarballs with gpg."""
    for ext in ("gz", "xz"):
        print(f"Signing {ext} tarball")
        subprocess.run(  # nosec
            [
                "gpg",
                "--armor",
                "--detach-sign",
                f"{tmpdir}/{tag}.tar.{ext}",
            ],
            check=True,
        )


def upload_tarballs(tag: str, tmpdir: str) -> None:
    """Upload the tarballs and signatures to GitHub."""
    content_type = {
        ".asc": "application/pgp-signature",
        "gz": "application/gzip",
        "xz": "application/x-xz",
    }
    for ext in ("gz", "xz"):
        for suffix in ("", ".asc"):
            filename = f"{tag}.tar.{ext}{suffix}"
            print(f"Uploading {filename} to GitHub release {tag}")
            with open(os.path.join(tmpdir, filename), "rb") as f:
                response = requests.post(
                    f"https://uploads.github.com/repos/TokTok/qTox/releases/{github.release_id(tag)}/assets",
                    headers={
                        "Content-Type": content_type[suffix or ext],
                        **github.auth_headers(required=True),
                    },
                    data=f,
                    params={"name": filename},
                )
                response.raise_for_status()


def main(config: Config) -> None:
    if config.upload:
        with tempfile.TemporaryDirectory() as tmpdir:
            create_tarballs(config.tag, tmpdir)
            sign_tarballs(config.tag, tmpdir)
            upload_tarballs(config.tag, tmpdir)
    else:
        create_tarballs(config.tag, ".")
        sign_tarballs(config.tag, ".")


if __name__ == "__main__":
    main(parse_args())
