#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2025 The TokTok team
import glob
import json
import multiprocessing
import subprocess  # nosec
import xml.dom.minidom as minidom  # nosec
from functools import cache as memoize
from typing import Any

import requests
from lib import stage

LANGUAGES = (
    "ar",
    "be",
    "bg",
    "bn",
    "cs",
    "da",
    "de",
    "el",
    "eo",
    "es",
    "et",
    "ja",
    "fa",
    "fi",
    "fr",
    "gl",
    "hr",
    "he",
    "hu",
    "is",
    "it",
    "lt",
    "lv",
    "ko",
    "kn",
    "mk",
    "nl",
    "nb_NO",
    "pl",
    "pt",
    "pt_BR",
    "ro",
    "ru",
    "si",
    "sk",
    "sl",
    "sq",
    "sr",
    "sv",
    "sw",
    "ta",
    "tr",
    "ug",
    "uk",
    "ur",
    "vi",
    "zh_CN",
    "zh_TW",
)

# LANGUAGES = ["jbo"]  # Uncomment to test Lojban translations.
LOCK = multiprocessing.Lock()


@memoize
def lupdate() -> str:
    """Return the path to the lupdate executable."""
    # If "lupdate" is in PATH, it will be used.
    if (subprocess.run(  # nosec
        ["which", "lupdate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
    ).returncode == 0):
        return "lupdate"
    # Check if we can find it in the Nix store.
    for path in glob.glob("/nix/store/*-qttools-*/bin/lupdate"):
        return path
    raise FileNotFoundError("lupdate not found")


def _normalize(text: str) -> str:
    """Normalize text for printing.

    Replace newlines with spaces and remove leading and trailing whitespace.
    """
    return text.replace("\n", " ").strip()


def _progress_ts(lang: str, current: int, total: int, text: str) -> None:
    """Print the progress of the translation.

    The progress is printed in a colorful message of the form

        "[ current/total ] (lang) text".

    The text is truncated to 80 characters.
    """
    progress = f"{current}/{total}"
    output = f"\r\033[1;34m[ {progress:4} ] ({lang})\033[0m {_normalize(text[:80])}"
    with LOCK:
        stage.clear()
        print(output, end="", flush=True)


def _progress_done(message: str) -> None:
    """Print a progress message indicating that the process is done."""
    output = f"\r\033[1;34m[  \033[1;32mOK  \033[1;34m]\033[0m {_normalize(message)}"
    with LOCK:
        stage.clear()
        print(output, flush=True)


def _fix_translation(source: str, text: str) -> str:
    """Fix common translation errors."""
    if not text:
        return text
    # These are %1, %2, etc. which are used for string formatting in Qt.
    # They only go up to 3 at the moment, but we'll be safe and go up to 6.
    for i in range(1, 6):
        if f"%{i}" in source:
            text = text.replace(f"% {i}", f"%{i}")
            if f"%{i}" not in text:
                raise ValueError(
                    f"Missing %{i} in translation of '{source}': '{text}'")
    if "%" in source:
        text = text.replace("%%", "%")
    return text


def _baidu_call_translate(lang: str, text: str) -> str:
    """Uses the Baidu Translate API to translate text to a given language.

    The source language is English. Baidu is decently good at translating
    Lojban. Google Translate doesn't support Lojban. OpenL is hilariously bad.
    E.g. it says that "vimcu lo citri" means "I will eat the lemon" when it
    actually means "remove the history".
    """
    response = requests.post(
        "https://fanyi.baidu.com/ait/text/translate",
        json={
            "domain": "common",
            "from": "en",
            "to": lang,
            "source": "web",
            "query": text,
        },
    )
    response.raise_for_status()
    events = (json.loads(line.removeprefix("data: "))
              for line in response.text.split("\n")
              if line.startswith("data: "))
    translations = (
        para["dst"] for event in events
        if event["data"]["event"] == "Translating" and event["data"]["list"]
        for para in event["data"]["list"])
    return "\n".join(translations)


def _baidu_translate(lang: str, text: str) -> str:
    attempt = _baidu_call_translate(lang, text)
    for i in range(1, 6):
        if f"%{i}" in text and f"% {i}" not in attempt and f"%{i}" not in attempt:
            return _baidu_call_translate(lang, text.replace("%", "%%"))
    return attempt


def _translate(lang: str, current: int, total: int, text: str) -> str:
    """Uses the Google Translate API to translate text to a given language.

    The source language is English.
    """
    _progress_ts(lang, current, total, text)
    if lang == "jbo":
        return _fix_translation(text, _baidu_translate("loj", text))
    response = requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={
            "client": "gtx",
            "sl": "en",
            "tl": lang,
            "dt": "t",
            "q": text,
        },
    )
    response.raise_for_status()
    return _fix_translation(text, "".join([x[0] for x in response.json()[0]]))


def _need_translation(source: str, translation: list[Any]) -> bool:
    if not translation:
        return False
    translated = translation[0].firstChild
    if isinstance(translated, minidom.Text):
        translated.data = _fix_translation(source, translated.data)
    if source == "LTR":
        # Skip the LTR/RTL context. We use it to control the UI. It
        # doesn't need to be translated.
        if isinstance(translated, minidom.Text):
            # Fix up any LTR/RTL values that are not "LTR" or "RTL".
            # We'll default to LTR if we don't know.
            if translated.data and translated.data not in ("LTR", "RTL"):
                translated.data = "LTR"
        return False
    return True


def _translate_ts_file(file: str) -> None:
    """Fill in the untranslated translations in a .ts file.

    Doesn't touch anything other than completely empty translations. Empty
    translations are marked with <translation></translation> or
    <translation type="unfinished"></translation>.
    """
    with open(file, "r") as f:
        dom = minidom.parse(f)  # nosec
    todo = []
    # <TS version="2.1" language="es_MX">
    lang = dom.getElementsByTagName("TS")[0].getAttribute("language")
    if not lang:
        raise ValueError(f"No language attribute found in TS file {file}")
    for context in dom.getElementsByTagName("context"):
        for message in context.getElementsByTagName("message"):
            source = message.getElementsByTagName("source")[0].firstChild
            if not isinstance(source, minidom.Text):
                continue
            translation = message.getElementsByTagName("translation")
            if not _need_translation(source.data, translation):
                continue
            # If the translation node text is empty, fill it in using the
            # translation of source. This is done for all translations that
            # are marked as "unfinished". If they are not marked as
            # "unfinished", empty is assumed to be intentional.
            if (translation[0].firstChild is None
                    and translation[0].getAttribute("type") == "unfinished"):
                todo.append((source.data, translation[0]))
    try:
        # Write out changes we may have made in the loop above.
        with open(file, "w") as f:
            dom.writexml(f)
        for i, (source, translation) in enumerate(todo):
            # Set the type attribute to "unfinished" to indicate that the
            # translation is not complete (it was automated).
            translation.setAttribute("type", "unfinished")
            translation.appendChild(
                dom.createTextNode(_translate(lang, i, len(todo), source)))
            # Commit to disk every time a translation is done so that we don't
            # lose progress if the script is interrupted.
            with open(file, "w") as f:
                dom.writexml(f)
    finally:
        # Run lupdate for formatting, even if the process is interrupted.
        _progress_ts(
            lang,
            len(todo),
            len(todo),
            subprocess.check_output(  # nosec
                [
                    lupdate(),
                    "src",
                    "-silent",
                    "-no-obsolete",
                    "-locations",
                    "none",
                    "-ts",
                    file,
                ],
                stderr=subprocess.STDOUT,
            ).decode("utf-8"),
        )


def _translate_language(lang: str) -> None:
    """Translate the strings in the .ts files for a given language."""
    _translate_ts_file(f"translations/{lang}.ts")


def main():
    with multiprocessing.Pool() as pool:
        pool.map(_translate_language, LANGUAGES)
    _progress_done("Translation done.")


if __name__ == "__main__":
    main()
