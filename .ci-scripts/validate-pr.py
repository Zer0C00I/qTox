#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 The TokTok team
import os
import re
import subprocess  # nosec
from functools import cache as memoize
from typing import Any
from typing import Optional

import requests

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
GIT_BASE_DIR = os.path.dirname(SCRIPT_DIR)


@memoize
def github_token() -> Optional[str]:
    token = os.getenv("GITHUB_TOKEN")
    if token:
        print("Authorization with GITHUB_TOKEN")
    else:
        print("Unauthorized (low rate limit applies)")
        print("Set GITHUB_TOKEN to increase the rate limit")
    return token


def auth_headers() -> dict[str, str]:
    token = github_token()
    if not token:
        return {}
    return {"Authorization": f"token {token}"}


def github_api_url() -> str:
    return os.getenv("GITHUB_API_URL") or "https://api.github.com"


github_api_requests: list[str] = []


@memoize
def github_api(url: str, params: tuple[tuple[str, str], ...] = tuple()) -> Any:
    """Calls the GitHub API with the given URL (GET only).

    Authorization is done with the GITHUB_TOKEN environment variable if it is set.
    """
    github_api_requests.append(f"GET {github_api_url()}{url}")
    response = requests.get(
        f"{github_api_url()}{url}",
        headers=auth_headers(),
        params=dict(params),
    )
    response.raise_for_status()
    return response.json()


def github_head_ref() -> str:
    """Calls git rev-parse --abbrev-ref HEAD to get the current branch name."""
    return (os.getenv("GITHUB_HEAD_REF") or subprocess.check_output(  # nosec
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        universal_newlines=True,
    ).strip())


def github_remote(remote: str) -> str:
    url = subprocess.check_output(  # nosec
        ["git", "remote", "get-url", remote],
        universal_newlines=True,
    ).strip()
    if "github.com" in url:
        return url.split(":")[-1].replace(".git", "")
    raise subprocess.CalledProcessError(1, "git remote get-url", url)


def github_actor() -> str:
    """Returns the GitHub username for the current repository."""
    return os.getenv("GITHUB_ACTOR") or github_remote("origin").split("/")[0]


def github_repository() -> str:
    return os.getenv("GITHUB_REPOSITORY") or github_remote("upstream")


def github_pr_number() -> int:
    """Calls the GitHub API to get the PR number for the current branch.

    Requires the GITHUB_API_URL and GITHUB_REF environment variables to be set.
    """
    return int(
        github_api(
            f"/repos/{github_repository()}/pulls",
            (("head", f"{github_actor()}:{github_head_ref()}"), ),
        )[0]["number"])


def github_ref_name() -> str:
    return os.getenv("GITHUB_REF_NAME") or f"{github_pr_number()}/merge"


def github_pr() -> Any:
    """Calls the GitHub API to get the current PR object."""
    return github_api(
        f"/repos/{github_repository()}/pulls/{github_ref_name().split('/')[0]}"
    )


def github_pr_branch() -> str:
    """Calls the GitHub API to get the branch name for the current PR."""
    return str(github_pr()["head"]["ref"])


def github_base_ref() -> str:
    """Calls the GitHub API to get the base branch for the current PR."""
    return os.getenv("GITHUB_BASE_REF") or str(github_pr()["base"]["ref"])


def git_remotes() -> list[str]:
    """Return a list of remote names (e.g. origin, upstream)."""
    return subprocess.check_output(  # nosec
        ["git", "remote"],
        universal_newlines=True,
    ).splitlines()


def github_base_branch() -> str:
    """Get the base ref with its remote path."""
    remotes = git_remotes()
    if "upstream" in remotes:
        return f"upstream/{github_base_ref()}"
    elif "origin" in remotes:
        return f"origin/{github_base_ref()}"
    raise subprocess.CalledProcessError(1, "git remote", "upstream or origin")


def print_check_start(name: str, description: str) -> None:
    """Prints a colorful message indicating that a check is starting.

    Does not print a newline at the end.

    Looks roughly like:
       [ .... ] Check name (requirement description)
    """
    print(f"\033[1;34m[ .... ]\033[0m {name} {description}", end="")


def print_check_end(name: str, description: str, success: bool) -> None:
    """Prints a colorful message indicating that a check has finished.

    Now it prints a newline at the end to get ready for the next check.

    Looks roughly like:
       [  OK  ] Check name (result description)
    """
    status = " \033[1;32mOK\033[0m " if success else "\033[1;31mFAIL\033[0m"
    print(f"\r\033[1;34m[ {status} \033[1;34m]\033[0m {name} {description}")


def padded(text: str, length: int) -> str:
    """Pads the text with spaces to the given length."""
    return f"{text}{' ' * (length - len(text))}"


class Checker:
    """A class to run checks and print colorful messages for the user."""

    def __init__(self, failures: list[str], name: str,
                 description: str) -> None:
        self.failures = failures
        self.name = name
        self.description = f"({description})"
        self.done = False

    def __enter__(self) -> "Checker":
        print_check_start(self.name, self.description)
        return self

    def ok(self, description: str) -> None:
        print_check_end(
            self.name,
            padded(f"({description})", len(self.description)),
            True,
        )
        self.done = True

    def fail(self, description: str) -> None:
        print_check_end(
            self.name,
            padded(f"({description})", len(self.description)),
            False,
        )
        self.failures.append(self.name)
        self.done = True

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if not self.done:
            self.fail("The check did not complete")


def github_weblate_prs() -> list[tuple[str, str]]:
    """List all the open Weblate PRs.

    Weblate PRs are those who are opened by the Weblate bot called "weblate".
    """
    return [(pr["title"], pr["html_url"])
            for pr in github_api(f"/repos/{github_repository()}/pulls")
            if pr["user"]["login"] == "weblate"]


def check_github_weblate_prs(failures: list[str]) -> None:
    """Check that all Weblate PRs are merged."""
    with Checker(failures, "Weblate PRs",
                 "All Weblate PRs should be merged") as check:
        weblate_prs = github_weblate_prs()
        if weblate_prs:
            check.fail("Some Weblate PRs are still open")
            for pr in weblate_prs:
                print(f"  - {pr[0]} ({pr[1]})")
        else:
            check.ok("All Weblate PRs are merged")


@memoize
def dockerfiles_dir() -> str:
    # Check if $GIT_BASE_DIR/../dockerfiles exists. If not, clone
    # https://github.com/TokTok/dockerfiles.git into .ci-scripts/dockerfiles.
    repo_dir = os.path.join(os.path.dirname(GIT_BASE_DIR), "dockerfiles")
    if not os.path.isdir(repo_dir):
        repo_dir = os.path.join(SCRIPT_DIR, "dockerfiles")
    if not os.path.isdir(repo_dir):
        subprocess.run(  # nosec
            [
                "git",
                "clone",
                "--depth=1",
                "https://github.com/TokTok/dockerfiles.git",
                repo_dir,
            ],
            check=True,
        )
    return repo_dir


def check_flathub_descriptor_dependencies(failures: list[str]) -> None:
    """Runs flatpak/update_flathub_descriptor_dependencies.py and checks if it made any changes."""
    with Checker(failures, "Flathub dependencies",
                 "Update flathub descriptor dependencies") as check:
        flathub_manifest_path = os.path.join(GIT_BASE_DIR, "flatpak",
                                             "io.github.qtox.qTox.json")
        subprocess.run(  # nosec
            [
                "flatpak/update_flathub_descriptor_dependencies.py",
                "--flathub-manifest",
                flathub_manifest_path,
                "--output",
                flathub_manifest_path,
                "--download-files-path",
                os.path.join(dockerfiles_dir(), "qtox", "download"),
                "--git-tag",
                f"v{github_pr_branch()}",
            ],
            check=True,
            cwd=GIT_BASE_DIR,
        )
        if subprocess.run(  # nosec
            ["git", "diff", "--exit-code", flathub_manifest_path]).returncode:
            check.fail("The flathub descriptor dependencies have changed")
            # Reset the changes to the flathub descriptor.
            subprocess.run(  # nosec
                ["git", "checkout", flathub_manifest_path],
                check=True,
            )
        else:
            check.ok("The flathub descriptor dependencies are up-to-date")


def check_toxcore_version(failures: list[str]) -> None:
    """Check that qtox/download/download_toxcore.sh is up-to-date.

    We get the latest release version of TokTok/c-toxcore from GitHub and
    compare it to the one in the script (which has a line like TOXCORE_VERSION=0.2.20).
    """
    with Checker(failures, "Toxcore version",
                 "Check if the toxcore version is up-to-date") as check:
        download_toxcore_path = os.path.join(dockerfiles_dir(), "qtox",
                                             "download", "download_toxcore.sh")
        with open(download_toxcore_path) as f:
            found = re.search(r"^TOXCORE_VERSION=(.*)$", f.read(),
                              re.MULTILINE)
            if not found:
                check.fail(
                    "Could not find the toxcore version in the download script"
                )
                return
            toxcore_version = found.group(1)

        latest_toxcore_version = github_api(
            "/repos/TokTok/c-toxcore/releases/latest")["tag_name"]
        if f"v{toxcore_version}" == latest_toxcore_version:
            check.ok(f"The toxcore version is up-to-date: {toxcore_version}")
        else:
            check.fail(
                f"The toxcore version is outdated: {toxcore_version} (latest: {latest_toxcore_version})"
            )


def check_package_versions(failures: list[str]) -> None:
    """Runs tools/update-versions.sh $GITHUB_PR_BRANCH and checks if it made any changes."""
    with Checker(failures, "Package versions",
                 "README and package versions should be up-to-date") as check:
        subprocess.run(  # nosec
            ["tools/update-versions.sh",
             github_pr_branch()],
            check=True,
            cwd=GIT_BASE_DIR,
        )
        diff = subprocess.run(["git", "diff", "--exit-code"])  # nosec
        if diff.returncode:
            check.fail("The package versions need to be updated")
            # Reset the changes to the README and package versions.
            subprocess.run(  # nosec
                [
                    "git",
                    "checkout",
                    "README.md",
                    "macos/Info.plist",
                    "res/io.github.qtox.qTox.appdata.xml",
                    "windows/qtox.nsi",
                    "windows/qtox64.nsi",
                ],
                cwd=GIT_BASE_DIR,
                check=True,
            )
        else:
            check.ok("The package versions are up-to-date")


def check_no_version_changes(failures: list[str]) -> None:
    """Check that no version changes are made in a non-release PR.

    Diff res/io.github.qtox.qTox.appdata.xml against $GITHUB_BASE_BRANCH and
    check if there's a line starting with "+" or "-" that contains a version
    number.

    Example:
    -  <release version="1.18.0-rc.3" date="2024-12-29"/>
    +  <release version="1.18.0" date="2024-12-29"/>
    """
    with Checker(
            failures,
            "No version changes",
            "No version changes should be made in a non-release PR",
    ) as check:
        diff = subprocess.check_output(  # nosec
            [
                "git",
                "diff",
                github_base_branch(),
                "--",
                "res/io.github.qtox.qTox.appdata.xml",
            ],
            cwd=GIT_BASE_DIR,
            universal_newlines=True,
        )
        minus = re.findall(r"^-[^<]+<release version=\"(.*)\" date", diff,
                           re.MULTILINE)
        plus = re.findall(r"^\+[^<]+<release version=\"(.*)\" date", diff,
                          re.MULTILINE)
        if minus and plus:
            check.fail("Version changes are not allowed"
                       f" in a non-release PR ({minus[0]} -> {plus[0]})")
        elif minus or plus:
            check.fail(
                "Removal or addition of a version number is not allowed"
                f" in a non-release PR ({minus[0] if minus else plus[0]})")
        else:
            check.ok("No version changes were made")


def main() -> None:
    """Main entry point."""
    print("GIT_BASE_DIR:       ", GIT_BASE_DIR)
    print("GITHUB_ACTOR:       ", github_actor())
    print("GITHUB_API_URL:     ", github_api_url())
    print("GITHUB_BASE_REF:    ", github_base_ref())
    print("GITHUB_BASE_BRANCH: ", github_base_branch())
    print("GITHUB_HEAD_REF:    ", github_head_ref())
    print("GITHUB_PR_BRANCH:   ", github_pr_branch())
    print("GITHUB_REF_NAME:    ", github_ref_name())
    print("GITHUB_REPOSITORY:  ", github_repository())

    print("\nRunning checks...\n")

    failures: list[str] = []

    # If the PR branch looks like a version number, do checks for a release PR.
    if re.match(r"^v?\d+\.\d+\.\d+", github_pr_branch()):
        print("This is a release PR.\n")
        check_github_weblate_prs(failures)
        check_flathub_descriptor_dependencies(failures)
        check_toxcore_version(failures)
        check_package_versions(failures)
    else:
        print("This is not a release PR.\n")
        check_no_version_changes(failures)

    print(f"\nDebug: {len(github_api_requests)} GitHub API requests made")

    if failures:
        print("\nSome checks failed:")
        for failure in failures:
            print(f"  - {failure}")
        exit(1)


if __name__ == "__main__":
    main()
