# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 The TokTok team
import re
import subprocess  # nosec
from dataclasses import dataclass
from functools import cache as memoize
from typing import Any
from typing import Optional

from lib import types

VERSION_REGEX = re.compile(r"v\d+\.\d+\.\d+(?:-rc\.\d+)?")
RELEASE_BRANCH_REGEX = re.compile(f"release/{VERSION_REGEX.pattern}")


@dataclass
class Version:
    major: int
    minor: int
    patch: int
    rc: Optional[int]

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}" + (
            f"-rc.{self.rc}" if self.rc is not None else "")

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        if self.rc is None:
            return other.rc is not None
        if other.rc is None:
            return False
        return self.rc < other.rc


def parse_version(version: str) -> Version:
    match = re.match(r"v(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?", version)
    if not match:
        raise ValueError(f"Could not parse version: {version}")
    return Version(
        major=int(match.group(1)),
        minor=int(match.group(2)),
        patch=int(match.group(3)),
        rc=int(match.group(4)) if match.group(4) else None,
    )


class Stash:

    def __init__(self) -> None:
        self.stashed = False

    def __enter__(self) -> None:
        if diff_exitcode():
            print("Stashing changes.")
            self.stashed = True
            subprocess.run(  # nosec
                [
                    "git",
                    "stash",
                    "--include-untracked",
                    "--quiet",
                ],
                check=True,
            )

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if self.stashed:
            print("Restoring stashed changes.")
            subprocess.run(  # nosec
                [
                    "git",
                    "stash",
                    "pop",
                    "--quiet",
                ],
                check=True,
            )


class Checkout:

    def __init__(self, branch: str) -> None:
        self.branch = branch
        self.old_branch = current_branch()

    def __enter__(self) -> None:
        if self.branch != current_branch():
            print(f"Checking out {self.branch} (from {self.old_branch}).")
            subprocess.run(  # nosec
                [
                    "git",
                    "checkout",
                    self.branch,
                    "--quiet",
                ],
                check=True,
            )

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if self.old_branch != current_branch():
            print(f"Moving back to {self.old_branch}.")
            subprocess.run(  # nosec
                [
                    "git",
                    "checkout",
                    self.old_branch,
                    "--quiet",
                ],
                check=True,
            )


class ResetOnExit:

    def __init__(self) -> None:
        self.branch = current_branch()

    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        subprocess.run(  # nosec
            [
                "git",
                "reset",
                "--hard",
                "--quiet",
            ],
            check=True,
        )


@memoize
def root() -> str:
    """Get the root directory of the git repository."""
    return (subprocess.check_output(  # nosec
        [
            "git",
            "rev-parse",
            "--show-toplevel",
        ]).strip().decode("utf-8"))


def fetch(*remotes: str) -> None:
    """Fetch tags and branches from a remote.

    Making sure our knowledge of the remote state is up-to-date. Fetches all
    branches, tags, and prunes stale references. Overwrites local tags if they
    have been updated on the remote.
    """
    subprocess.run(  # nosec
        [
            "git",
            "fetch",
            "--tags",
            "--prune",
            "--force",
            "--quiet",
            "--multiple",
            *remotes,
        ],
        check=True,
    )


def remote_slug(remote: str) -> types.RepoSlug:
    """Get the GitHub slug of a remote."""
    url = (
        subprocess.check_output(  # nosec
            [
                "git",
                "remote",
                "get-url",
                remote,
            ]).strip().decode("utf-8"))
    match = re.search(r"[:/]([^/]+)/([^.]+)(?:\.git)?", url)
    if not match:
        raise ValueError(f"Could not parse remote URL: {url}")
    return types.RepoSlug(match.group(1), match.group(2))


def remotes() -> list[str]:
    """Return a list of remote names (e.g. origin, upstream)."""
    return subprocess.check_output(  # nosec
        ["git", "remote"],
        universal_newlines=True,
    ).splitlines()


def branch_sha(branch: str) -> str:
    """Get the SHA of a branch."""
    return (subprocess.check_output(  # nosec
        [
            "git",
            "rev-parse",
            branch,
        ]).strip().decode("utf-8"))


def branches(remote: Optional[str] = None) -> list[str]:
    """Get a list of branches, optionally from a remote.

    If remote is None, return local branches.
    """
    if remote is not None and remote not in remotes():
        raise ValueError(f"Remote {remote} does not exist.")
    bs = subprocess.check_output(  # nosec
        [
            "git",
            "branch",
            "--list",
            "--no-column",
            "--format=%(refname:short)",
        ] + ([] if remote is None else ["--remotes"]),
        universal_newlines=True,
    ).splitlines()
    if remote is None:
        return bs
    return [b.split("/", 1)[1] for b in bs if b.startswith(f"{remote}/")]


def current_branch() -> str:
    """Get the current branch name."""
    return (subprocess.check_output(  # nosec
        [
            "git",
            "rev-parse",
            "--abbrev-ref",
            "HEAD",
        ]).strip().decode("utf-8"))


def release_tags() -> list[str]:
    tags = subprocess.check_output(["git", "tag", "--merged"])  # nosec
    return sorted(
        (tag for tag in tags.decode("utf-8").splitlines()
         if re.match(VERSION_REGEX, tag)),
        reverse=True,
        key=parse_version,
    )


def release_branches() -> list[str]:
    """Get a list of release branches."""
    return [b for b in branches() if re.match(RELEASE_BRANCH_REGEX, b)]


def diff_exitcode(*args: str) -> bool:
    """Check if there are any changes in the git working directory."""
    return (subprocess.run(  # nosec
        [
            "git",
            "diff",
            "--exit-code",
            "--quiet",
            *args,
        ],
        check=False,
    ).returncode != 0)


def is_clean() -> bool:
    """Check if the git working directory is clean.

    No pending or staged changes.
    """
    return not diff_exitcode() and not diff_exitcode("--cached")


def current_tag() -> str:
    """Get the most recent tag."""
    return (subprocess.check_output(  # nosec
        [
            "git",
            "describe",
            "--tags",
            "--abbrev=0",
            "--match",
            "v*",
        ]).decode("utf-8").strip())


def checkout(branch: str) -> None:
    """Checkout a branch."""
    subprocess.run(  # nosec
        [
            "git",
            "checkout",
            branch,
            "--quiet",
        ],
        check=True,
    )


def revert(*files: str) -> None:
    """Checkout files."""
    branch = current_branch()
    subprocess.run(  # nosec
        [
            "git",
            "checkout",
            branch,
            "--quiet",
            "--",
            *files,
        ],
        check=True,
    )


def add(*files: str) -> None:
    """Add files to the index."""
    subprocess.run(  # nosec
        [
            "git",
            "add",
            *files,
        ],
        check=True,
    )


def reset(branch: str) -> None:
    """Reset a branch to a specific commit."""
    subprocess.run(  # nosec
        [
            "git",
            "reset",
            "--hard",
            branch,
            "--quiet",
        ],
        check=True,
    )


def create_branch(branch: str, base: str) -> None:
    """Create a branch from a base branch."""
    subprocess.run(  # nosec
        [
            "git",
            "checkout",
            "-b",
            branch,
            base,
            "--quiet",
        ],
        check=True,
    )


def list_changed_files() -> list[str]:
    """List all files that have been changed."""
    return subprocess.check_output(  # nosec
        [
            "git",
            "diff",
            "--name-only",
        ],
        universal_newlines=True,
    ).splitlines()


def commit(title: str, body: str) -> None:
    """Commit changes."""
    subprocess.run(  # nosec
        [
            "git",
            "commit",
            "--quiet",
            "--message",
            title,
            "--message",
            body,
        ],
        check=True,
    )
