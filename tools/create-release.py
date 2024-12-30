#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 The TokTok team
import argparse
import os
import re
import subprocess  # nosec
from dataclasses import dataclass
from typing import Optional

from lib import changelog
from lib import git
from lib import github
from lib import stage


@dataclass
class Config:
    branch: str
    dryrun: bool
    force: bool
    production: bool
    rebase: bool
    resume: bool


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="""
    Run a bunch of checks to validate a PR. This script is meant to be run in a
    GitHub Actions workflow, but can also be run locally.
    """)
    parser.add_argument(
        "--branch",
        help="The branch to build the release from. Default: master",
        default="upstream/master",
    )
    parser.add_argument(
        "--dryrun",
        action=argparse.BooleanOptionalAction,
        help="Do not push changes to origin.",
        default=False,
    )
    parser.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        help="Force-push the release branch to origin (default on).",
        default=True,
    )
    parser.add_argument(
        "--production",
        action=argparse.BooleanOptionalAction,
        help=
        "Build a production release. If false (default), build a release candidate.",
        default=False,
    )
    parser.add_argument(
        "--rebase",
        action=argparse.BooleanOptionalAction,
        help="Rebase the release branch onto the base branch (default on).",
        default=True,
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        help="Skip manual input steps where possible.",
        default=False,
    )
    return Config(**vars(parser.parse_args()))


def require(condition: bool, message: Optional[str] = None) -> None:
    if not condition:
        raise stage.InvalidState(message or "Requirement not met")


def stage_version(config: Config) -> str:
    with stage.Stage(
            "Fetch upstream",
            "Fetching tags and branches from origin and upstream") as s:
        git.fetch("origin", "upstream")
        s.ok(git.branch_sha("upstream/master")[:7])
    with stage.Stage("Version", "Determine the upcoming version") as s:
        version = github.next_milestone()
        if not config.production:
            # This is a prerelease, so we need to find the latest prerelease.
            rc = max(github.release_candidates(version), default=0)
            version = f"{version}-rc.{rc + 1}"
        require(re.match(r"v\d+\.\d+\.\d+(?:-rc\.\d+)?", version) is not None)
        s.ok(version)
    return version


def release_commit_message(version: str) -> str:
    return f"chore: Release {version}"


def stage_branch(config: Config, version: str) -> None:
    with stage.Stage("Create release branch",
                     "Creating a release branch") as s:
        release_branch = f"release/{version}"
        if release_branch in git.branches() or release_branch in git.branches(
                "origin"):
            git.checkout(release_branch)
            if not config.rebase:
                action = "skipping rebase"
            else:
                rebased = git.last_commit_message(
                    release_branch) == release_commit_message(version)
                if rebased:
                    if git.rebase(config.branch, commits=1):
                        action = f"rebased onto {config.branch}"
                    else:
                        action = f"already on {config.branch}"
                else:
                    git.reset(config.branch)
                    action = f"reset to {config.branch}"
            s.ok(f"Branch '{release_branch}' already exists; {action}")
        else:
            git.create_branch(release_branch, config.branch)
            s.ok(f"Branch '{release_branch}' created")
        require(git.current_branch() == release_branch, git.current_branch())


def stage_validate() -> None:
    subprocess.run(["tools/validate-pr.py", "--commit"], check=True)  # nosec


def stage_release_notes(config: Config, version: str) -> None:
    """Opens $EDITOR (from environment, or vim) to edit the release notes in CHANGELOG.md."""
    with stage.Stage("Write release notes", "Opening editor") as s:
        if config.resume and changelog.has_release_notes(version):
            s.ok("Skipping")
        else:
            editor = os.getenv("EDITOR") or "vim"
            subprocess.run([editor, "CHANGELOG.md"], check=True)  # nosec
            git.add("CHANGELOG.md")
            s.ok()


def stage_commit(version: str) -> None:
    with stage.Stage("Commit changes", "Committing changes") as s:
        release_notes = changelog.get_release_notes(version)
        if git.is_clean():
            s.ok("No changes to commit")
        else:
            changes = git.changed_files()
            git.commit(release_commit_message(version), release_notes)
            s.ok(str(changes))


def stage_push(config: Config) -> None:
    with stage.Stage("Push changes", "Pushing changes to origin") as s:
        if config.dryrun:
            s.ok("Dry run; not pushing changes")
        else:
            git.push("origin", git.current_branch(), force=config.force)
            s.ok()


RELEASER_START = "<!-- Releaser:start -->"
RELEASER_END = "<!-- Releaser:end -->"


def get_pr_body(body: str) -> str:
    """
    <!-- Releaser:start -->
    Actual body goes here.
    <!-- Releaser:end -->
    """
    start = body.find(RELEASER_START)
    end = body.find(RELEASER_END)
    if start == -1 or end == -1:
        return ""
    return body[start + len(RELEASER_START):end].strip()


def patch_pr_body(body: str, patch: str) -> str:
    start = body.find(RELEASER_START)
    end = body.find(RELEASER_END)
    if start == -1 or end == -1:
        return f"{RELEASER_START}\n{patch}\n{RELEASER_END}\n{body}"
    return f"{body[:start]}{RELEASER_START}\n{patch}\n{RELEASER_END}\n{body[end + len(RELEASER_END):]}"


def stage_pull_request(
    config: Config,
    version: str,
) -> Optional[github.PullRequest]:
    with stage.Stage("Create pull request",
                     "Creating a pull request on GitHub") as s:
        title = f"chore: Release {version}"
        body = changelog.get_release_notes(version)
        head = f"{github.actor()}:release/{version}"
        base = "master"
        if config.dryrun:
            s.ok("Dry run; not creating a pull request")
            print(f"title: {title}")
            print(f"body: {body}")
            print(f"head: {head}")
            print(f"base: {base}")
            return None

        existing_pr = github.find_pr(head, base)
        if existing_pr:
            if (existing_pr.state == "open" and existing_pr.title == title
                    and get_pr_body(existing_pr.body) == body):
                s.ok(f"PR already exists: {existing_pr.html_url}")
                return existing_pr

            github.change_pr(
                existing_pr.number,
                {
                    "state": "open",
                    "title": title,
                    "body": patch_pr_body(existing_pr.body, body),
                },
            )
            s.ok(f"Modified PR: {existing_pr.html_url}")
            return existing_pr

        pr = github.create_pr(title, patch_pr_body("", body), head, base)
        s.ok(pr.html_url)
        return pr


def stage_restyled(config: Config, version: str, parent: stage.Stage) -> None:
    with stage.Stage("Restyled", "Applying restyled fixes",
                     parent=parent) as s:
        subprocess.run(["hub-restyled"], check=True)  # nosec
        if git.is_clean():
            raise s.fail("Failed to apply restyled changes")
        git.add(".")
        stage_commit(version)
        stage_push(config)
        s.ok("Restyled changes applied")


def get_head_pr(s: stage.Stage, version: str) -> github.PullRequest:
    for _ in range(10):
        pr = github.find_pr(f"{github.actor()}:release/{version}", "master")
        if pr:
            sha = git.branch_sha(f"release/{version}")
            if pr.head_sha == sha:
                return pr
            s.progress(f"Waiting for {pr.head_sha} to match {sha}")
        stage.sleep(5)
    raise ValueError("Timeout waiting for PR to be created/updated")


def stage_await_checks(config: Config, version: str) -> None:
    with stage.Stage("Await checks", "Waiting for checks to pass") as s:
        for _ in range(20):  # 20 * 30s = 10 minutes
            pr = get_head_pr(s, version)

            checks = github.checks(pr.head_sha)
            if not checks:
                s.progress("Awaiting checks to start")
                stage.sleep(10)
                continue

            completed = len(
                [c for c in checks.values() if c.status == "completed"])
            progress = len(
                [c for c in checks.values() if c.status == "in_progress"])
            success = len(
                [c for c in checks.values() if c.conclusion == "success"])
            failures = len(
                [c for c in checks.values() if c.conclusion == "failure"])
            neutral = len(
                [c for c in checks.values() if c.conclusion == "neutral"])

            if completed == len(checks):
                if failures:
                    raise s.fail(f"{failures} checks failed")
                s.ok(f"All {completed} checks passed")
                return

            s.progress(f"{success} checks passed"
                       f", {neutral} checks neutral"
                       f", {failures} failed"
                       f", {progress} in progress")
            if ("common / restyled" in checks
                    and checks["common / restyled"].conclusion == "failure"):
                stage_restyled(config, version, parent=s)

            stage.sleep(30)

        raise s.fail("Timeout waiting for checks to pass")


def stage_await_mergeable(config: Config, version: str) -> None:
    with stage.Stage("Await mergeable",
                     "Waiting for the PR to be mergeable") as s:
        for _ in range(20):  # 20 * 30s = 10 minutes
            pr = get_head_pr(s, version)
            if pr.mergeable:
                s.ok("PR is mergeable")
                return
            s.progress("PR is not yet mergeable")
            stage.sleep(30)
        raise s.fail("Timeout waiting for PR to be mergeable")


def run_stages(config: Config) -> None:
    require(git.current_branch() == config.branch)
    require(git.is_clean())

    version = stage_version(config)
    if release_commit_message(version) not in git.log("master"):
        stage_branch(config, version)
        stage_validate()
        stage_release_notes(config, version)
        stage_commit(version)
        stage_push(config)
        stage_pull_request(config, version)
        stage_await_checks(config, version)
        stage_await_mergeable(config, version)
    else:
        print(f"Release branch release/{version} already merged.")
        # TODO(iphydf): Implement the next steps after this.
        return


def main(config: Config) -> None:
    # chdir into the root of the repository.
    os.chdir(git.root())
    # We need auth to get the draft release etc.
    github.auth_headers(required=True)
    try:
        # Stash any local changes for the user to later resume working on.
        with git.Stash():
            # We need to be on master to create a release, but we want to
            # return to the original branch afterwards.
            with git.Checkout(config.branch):
                # Undo any partial changes if the script is aborted.
                with git.ResetOnExit():
                    run_stages(config)
    except stage.UserAbort:
        print("User aborted the program.")
        return


if __name__ == "__main__":
    main(parse_args())
