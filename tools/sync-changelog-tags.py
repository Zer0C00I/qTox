#!/usr/bin/env python3
"""Updates the tag messages of the git tags in the repository to match the
corresponding entries in the CHANGELOG.md file.

It does this by parsing the CHANGELOG.md file and comparing the tag messages
with the corresponding entries in the CHANGELOG.md file.

If the tag message contains an "Original tagger: " line, the original tagger
is preserved in the updated tag message.
"""
import argparse
import re
import subprocess  # nosec
from dataclasses import dataclass

from lib import changelog


@dataclass
class Config:
    sign: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="""
    Updates the tag messages of the git tags in the repository to match the
    corresponding entries in the CHANGELOG.md file.
    """)
    parser.add_argument(
        "--sign",
        action=argparse.BooleanOptionalAction,
        help="Sign tags (doesn't work on GitHub Actions)",
        default=True,
        dest="sign",
    )
    return parser.parse_args()


def git_tag_message(tag: str) -> tuple[str, str, str]:
    tag_info = subprocess.check_output(  # nosec
        [
            "git",
            "cat-file",
            "tag",
            tag,
        ]).decode("utf-8")
    sha_found = re.search(r"^object (\w+)$", tag_info, re.MULTILINE)
    if not sha_found:
        raise Exception(f"SHA hash not found for tag {tag}")
    sha = sha_found.group(1)

    tagger_found = re.search(r"^tagger (.+)$", tag_info, re.MULTILINE)
    if not tagger_found:
        raise Exception(f"Tagger not found for tag {tag}")
    tagger = tagger_found.group(1)

    if "-----BEGIN PGP SIGNATURE-----" in tag_info:
        message_found = re.search(
            r"\n\n((.|\n)*)\n-----BEGIN PGP SIGNATURE-----", tag_info,
            re.MULTILINE)
    else:
        message_found = re.search(r"\n\n((.|\n)*)$", tag_info, re.MULTILINE)
    if not message_found:
        raise Exception(f"Message not found for tag {tag}")
    message = message_found.group(1).strip()

    # If there's an "Original tagger: " line in the message, extract the original tagger
    original_tagger_found = re.search(r"\nOriginal tagger: (.+)$", message,
                                      re.MULTILINE)
    if original_tagger_found:
        tagger = original_tagger_found.group(1)
        message = re.sub(r"\n+Original tagger: .+$", "", message, re.MULTILINE)
    return sha, tagger, message


def git_tag_update(config: Config, tag: str, sha: str, message: str) -> None:
    cmd = ["git", "tag", "-f", "-a", tag, "-m", message, sha]
    if config.sign:
        cmd.insert(2, "-s")
    subprocess.run(cmd, check=True)  # nosec


def main(config: Config) -> None:
    for version, message in changelog.parse().items():
        if not message.strip():
            continue
        sha, tagger, orig_message = git_tag_message(version)
        if orig_message == message:
            continue
        message = f"{message}\n\nOriginal tagger: {tagger}"
        print("--------------------")
        print(f"Updating tag message for {version}"
              f"\n>>>>>>>>\n{orig_message}\n========\n"
              f"{message}\n<<<<<<<<")
        git_tag_update(config, version, sha, message)


if __name__ == "__main__":
    main(Config(**vars(parse_args())))
