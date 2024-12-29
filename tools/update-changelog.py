#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 The TokTok team
import pathlib
import re
import subprocess  # nosec
import tomllib
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Iterable
from typing import Optional

# b2215454e chore(windows): update copyright year
# d44fc4dfe chore: Add script for syncing CHANGELOG.md to git tags.
COMMIT_REGEX = re.compile(
    r"(?P<category>(?:chore|fix|feat|perf|docs|refactor|revert|test|style)):?(?:\((?P<module>[^)]+)\))?:\s*(?P<message>.+)"
)

# 977b7fc9a02b2b44164ffb77ab35f4cdfae90542
# Author: sudden6 <sudden6@gmx.at>
# Date:   Sat Jun 23 15:18:12 2018 +0200
#
#     fix(settings): automatically disable UDP when a proxy is set
#
#     fixes: #5174
LOG_REGEX = re.compile(
    r"^(?P<sha>[0-9a-f]+)(?:\nMerge:(?: [0-9a-f]+)+)?\nAuthor: (?P<author>.+)\nDate:   (?P<date>.+)\n\n(?P<message>(?:.|\n)+)",
    re.MULTILINE,
)

CATEGORIES = ["feat", "fix", "perf"]


def category_name(category: str) -> str:
    return {
        "feat": "Features",
        "fix": "Bug Fixes",
        "perf": "Performance",
        "docs": "Documentation",
        "style": "Styles",
        "refactor": "Code Refactoring",
        "test": "Tests",
        "chore": "Chores",
        "revert": "Reverts",
        "misc": "Miscellaneous",
    }[category]


@dataclass
class LogEntry:
    repository: str
    sha: str
    author: str
    date: str
    category: str
    module: Optional[str]
    message: str
    closes: tuple[str, ...]


@dataclass
class ForkInfo:
    repository: str
    since: str


@dataclass
class Config:
    changelog: Optional[str]
    repository: str
    forked_from: list[ForkInfo]
    ignore_before: Optional[str]


def parse_fork_config(data: list[dict[str, Any]]) -> list[ForkInfo]:
    return [
        ForkInfo(repository=d["repository"], since=d["since"]) for d in data
    ]


def parse_config(data: dict[str, Any]) -> Config:
    return Config(
        changelog=data.get("clog", {}).get("changelog", None),
        repository=data.get("clog", {}).get("repository", "http://localhost/"),
        forked_from=parse_fork_config(
            data.get("clog", {}).get("forked-from", {})),
        ignore_before=data.get("clog", {}).get("ignore-before", None),
    )


def git_release_tags() -> list[str]:
    tags = subprocess.check_output(["git", "tag", "--merged"])  # nosec
    return sorted(
        (tag for tag in tags.decode("utf-8").splitlines()
         if tag.startswith("v") and "-rc" not in tag),
        reverse=True,
        key=lambda tag: tuple(map(int, tag[1:].split("."))),
    )


def git_log(prev_tag: str, cur_tag: str) -> list[str]:
    log = subprocess.check_output([  # nosec
        "git",
        "log",
        f"{prev_tag}..{cur_tag}",
    ])
    return log.decode("utf-8").removeprefix("commit ").split("\ncommit ")


def git_tag_info(tag: str) -> tuple[str, str]:
    tag_data = subprocess.check_output(  # nosec
        [
            "git",
            "cat-file",
            "tag",
            tag,
        ]).decode("utf-8")
    date_match = re.search(r"^Original tagger: .+ (\d{10})", tag_data,
                           re.MULTILINE)
    if not date_match:
        date_match = re.search(r"^tagger .+ (\d{10})", tag_data, re.MULTILINE)
    if not date_match:
        raise Exception(f"Date not found for tag {tag}")

    if "-----BEGIN PGP SIGNATURE-----" in tag_data:
        message_match = re.search(
            r"\n\n((.|\n)*)\n-----BEGIN PGP SIGNATURE-----", tag_data,
            re.MULTILINE)
    else:
        message_match = re.search(r"\n\n((.|\n)*)$", tag_data, re.MULTILINE)
    if not message_match:
        raise Exception(f"Message not found for tag {tag}")

    message = re.sub(r"\n+Original tagger: .+$", "",
                     message_match.group(1).strip(), re.MULTILINE)
    return (
        datetime.fromtimestamp(int(date_match.group(1))).strftime("%Y-%m-%d"),
        message,
    )


def unindent(text: str) -> str:
    lines = text.split("\n")
    indent = len(lines[0]) - len(lines[0].lstrip())
    return "\n".join(line[indent:].rstrip() for line in lines)


def parse_closes(message: str) -> list[str]:
    return [
        fix for fixes in re.findall(
            r"(?:closes|fix|fixe[ds]|resolve[ds]):?\s+((?:#\d+(?:,\s*)?)+)",
            message,
            re.IGNORECASE,
        ) for fix in re.findall(r"#(\d+)", fixes)
    ]


def next_repo(repo: str, forks: list[ForkInfo], sha: str) -> str:
    for fork in forks:
        if sha.startswith(fork.since):
            return fork.repository
    return repo


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class LogParser:

    def __init__(self, config: Config) -> None:
        self.config = config
        self.repository = config.repository

    def parse_log(self, log: list[str]) -> list[LogEntry]:
        """
        a83ef30476012d3840582ddea64cf180285beb4f
        Author: Anthony Bilinski <me@abilinski.com>
        Date:   Sat Mar 5 04:20:45 2022 -0800

            chore(release): Add changelog
        """
        entries = []
        for entry in log:
            matches = re.match(LOG_REGEX, entry)
            if not matches:
                raise Exception(f"Failed to parse log entry: {entry}")
            sha = matches.group("sha")
            self.repository = next_repo(self.repository,
                                        self.config.forked_from, sha)
            author = matches.group("author")
            date = matches.group("date")
            split = unindent(matches.group("message")).split("\n\n", 1)
            first, rest = (split[0], "") if len(split) == 1 else split
            if (first.startswith("Merge ") or first.startswith("Revert ")
                    or first.startswith("Update ")):
                continue
            parsed = re.match(COMMIT_REGEX, normalize_space(first))
            closes = tuple(
                sorted(set(parse_closes(first) + parse_closes(rest))))
            if parsed:
                entries.append(
                    LogEntry(
                        repository=self.repository,
                        sha=sha,
                        author=author,
                        date=date,
                        closes=closes,
                        **parsed.groupdict(),
                    ))
            else:
                entries.append(
                    LogEntry(
                        repository=self.repository,
                        sha=sha,
                        author=author,
                        date=date,
                        category="misc",
                        module=None,
                        message=first,
                        closes=closes,
                    ))
        return entries


def group_by_category(entries: list[LogEntry]) -> dict[str, list[LogEntry]]:
    grouped: dict[str, list[LogEntry]] = {}
    for entry in entries:
        if entry.category not in grouped:
            grouped[entry.category] = []
        grouped[entry.category].append(entry)
    return grouped


def group_by_message(entries: list[LogEntry]) -> dict[str, list[LogEntry]]:
    by_message: dict[str, list[LogEntry]] = {}
    for entry in entries:
        if entry.message not in by_message:
            by_message[entry.message] = []
        by_message[entry.message].append(entry)
    return by_message


def group_by_module(
    entries: list[LogEntry],
) -> dict[Optional[str], dict[str, list[LogEntry]]]:
    by_module: dict[Optional[str], list[LogEntry]] = {}
    for entry in entries:
        if entry.module not in by_module:
            by_module[entry.module] = []
        by_module[entry.module].append(entry)
    return {
        module: group_by_message(entries)
        for module, entries in by_module.items()
    }


def format_closes(entry: LogEntry) -> str:
    message = ""
    for issue in entry.closes:
        message += f", closes [#{issue}]({entry.repository}/issues/{issue})"
    return message


MARKDOWN_REGEX = re.compile(
    r"`[^`]+`|\*\*[^\*]+\*\*|\*[^\*]+\*|_[^_]+_|~[^~]+~|\S+|\s+")


def is_xml_tag(word: str) -> bool:
    return word.startswith("<") and word.endswith(">")


def escape(word: str) -> str:
    if word.startswith("`") and word.endswith("`"):
        return word
    if word == "*":
        return "\\*"
    if word == "<":
        return "&lt;"
    if word == ">":
        return "&gt;"
    if "_" in word or is_xml_tag(word) or "::" in word:
        return f"`{word}`"
    if word.count("*") % 2:
        return word.replace("*", "\\*")
    return word


def format_message(entry: LogEntry) -> str:
    return "".join(
        escape(word) for word in re.findall(MARKDOWN_REGEX, entry.message))


def format_entry(entries: list[LogEntry]) -> str:
    if not entries:
        raise ValueError("No entries")
    shas = ", ".join(
        f"([{entry.sha[:8]}]({entry.repository}/commit/{entry.sha}){format_closes(entry)})"
        for entry in entries)
    return f"{format_message(entries[0])} {shas}"


def format_changelog(
    tag: str,
    groups: dict[str, dict[Optional[str], dict[str, list[LogEntry]]]],
) -> str:
    """
    <a name="v1.17.5"></a>

    ## v1.17.5 (2022-03-05)

    #### Bug Fixes

    - Update video API usage for newer libavcodec ([f5fabc2f](https://github.com/qTox/qTox/commit/f5fabc2fe24b6f01e47a527b982395a5305d31f6))
    - **Windows:**
    - Restrict non-default install directory permissions ([553bd47e](https://github.com/qTox/qTox/commit/553bd47e8171fd4f15e062e4faf734e32002f6fb))
    - Build NSIS installer in Unicode mode ([9f84184b](https://github.com/qTox/qTox/commit/9f84184ba815bfc892691fa611c6756721ba1333))
    - Define installer language before trying to access it ([1353fc93](https://github.com/qTox/qTox/commit/1353fc934ed70e9bfab3e50e42dba5eb139cd59e))

    #### Features

    - **Settings:** Add setting for hiding group join and leave system messages ([916e797c](https://github.com/qTox/qTox/commit/916e797c10d10ba556e9a3339353f1bd97663d15))
    - **UI:** Add UI For controlling group join and leave system messages setting ([423049db](https://github.com/qTox/qTox/commit/423049db50ffea14ec222e1a83ee976029a6afaf))
    - **chatlog:** Disable join and leave system messages based on setting ([ee0334ac](https://github.com/qTox/qTox/commit/ee0334acc55215ed8e94bae8fa4ff8976834af20))
    """
    tag_date, tag_message = git_tag_info(tag)
    lines = [
        f'<a name="{tag}"></a>',
        "",
        f"## {tag} ({tag_date})",
    ]
    if tag_message:
        lines.append("")
        lines.append(tag_message)
    for category, entries in groups.items():
        if category not in CATEGORIES:
            continue
        lines.append("")
        lines.append(f"#### {category_name(category)}")
        lines.append("")
        for module, module_entries in sorted(entries.items(),
                                             key=lambda x: x[0] or ""):
            if module is None:
                for entry in module_entries.values():
                    lines.append(f"- {format_entry(entry)}")
            elif len(module_entries) == 1:
                for entry in module_entries.values():
                    lines.append(f"- **{module}:** {format_entry(entry)}")
            else:
                lines.append(f"- **{module}:**")
                for entry in module_entries.values():
                    lines.append(f"  - {format_entry(entry)}")
    return "\n".join(lines)


def generate_changelog(parser: LogParser, cur_tag: str,
                       prev_tag: str) -> Optional[str]:
    log = git_log(prev_tag, cur_tag)
    if not any(log):
        log = []
    groups = {
        k: group_by_module(v)
        for k, v in group_by_category(parser.parse_log(log)).items()
    }
    return format_changelog(cur_tag, groups)


def filter_str(strings: Iterable[Optional[str]]) -> Iterable[str]:
    return (s for s in strings if s)


def find_clog_toml() -> Optional[pathlib.Path]:
    """Find .clog.toml in the parent directories."""
    path = pathlib.Path(__file__)
    # Find the .clog.toml file in the parent directories
    # (excluding the root directory).
    while path != path.parent:
        if (path / ".clog.toml").is_file():
            return path / ".clog.toml"
        path = path.parent
    return None


def read_clog_toml() -> dict[str, Any]:
    toml = find_clog_toml()
    if not toml:
        return {}
    with open(toml, "rb") as f:
        return tomllib.load(f)


def main() -> None:
    config = parse_config(read_clog_toml())
    tags = git_release_tags()
    # Ignore everything before and including some tag.
    # (+1 because we still need {after tag}...{tag}).
    if config.ignore_before:
        tags = tags[:tags.index(config.ignore_before) + 1]
    parser = LogParser(config)
    changelog = "\n\n".join(
        filter_str(
            generate_changelog(parser, t[0], t[1])
            for t in zip(tags, tags[1:])))

    if config.changelog:
        with open(config.changelog, "w") as f:
            print(changelog, file=f)
    else:
        print(changelog)


if __name__ == "__main__":
    main()
