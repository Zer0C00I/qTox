#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2025 The TokTok team
import glob
import os
import random
import re
import subprocess  # nosec
import xml.dom.minidom as minidom  # nosec
from functools import cache as memoize

# <TS version="2.1" language="pr" sourcelanguage="en_US">
# <context>
#     <name>AVForm</name>
#     <message>
#         <source>Audio/Video</source>
#         <translation>Scryin&apos;</translation>
#     </message>
#     <message>
#         <source>Confirmation</source>
#         <translation type="unfinished"></translation>
#     </message>
# </context>
# </TS>


def send_ai_prompt(text: str) -> None:
    """Sends a prompt to the AI and returns the response."""
    print(text)


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


def accept_ai_response(response_file: str) -> None:
    """Accepts the AI response and updates the translations.

    Responses look like this:
        <source>This month</source>
        <translation>This moon</translation>

        <source>Here is a multi
        line source.</source>
        <translation>Yer be a multi
        line sear.</translation>

    If the translation is the same as the source, we ignore it.
    """
    xml = minidom.parse("translations/pr.ts")  # nosec
    with open(response_file, "r") as f:
        response = f.read()
    translations = {}
    for source, translation in re.findall(
            r"<source>(.*?)</source>\s*<translation>(.*?)</translation>",
            response,
            re.DOTALL,
    ):
        if source == "LTR":
            # Ignore special string.
            continue
        if source == translation:
            continue
        translations[source] = translation
    for context in xml.getElementsByTagName("context"):
        for message in context.getElementsByTagName("message"):
            source = message.getElementsByTagName("source")[0].firstChild
            if not isinstance(source, minidom.Text):
                continue
            translation = message.getElementsByTagName("translation")[0]
            if translation.getAttribute("type") == "unfinished":
                if source.data in translations and not translation.firstChild:
                    translation.appendChild(
                        xml.createTextNode(translations[source.data]))

    with open("translations/pr.ts", "w") as f:
        xml.writexml(f)

    subprocess.check_output(  # nosec
        [
            lupdate(),
            "src",
            "-silent",
            "-no-obsolete",
            "-locations",
            "none",
            "-ts",
            "translations/pr.ts",
        ])


def main() -> None:
    """Generates an AI prompt for translating the Tox client from English to Pirate English.

    Usage:
      tools/translate_ai.py > request.txt
      # Do something with request.txt (e.g. paste it into ChatGPT).
      # Put the response from ChatGPT into response.txt.
      tools/translate_ai.py > request.txt  # Now this will process response.txt.
      # Repeat :)
    """
    # if response.txt exists, accept the response and update the translations.
    if os.path.exists("response.txt"):
        accept_ai_response("response.txt")
    ai_prompt = """Please help me translate these strings from English to Pirate English.
First, here are some examples of translations that have already been done:

```
"""

    # 2. get all source/translation pairs where the translation is not empty. Give them to the AI
    # as example translations.
    examples = []
    dom = minidom.parse("translations/pr.ts")  # nosec
    for context in dom.getElementsByTagName("context"):
        for message in context.getElementsByTagName("message"):
            source = message.getElementsByTagName("source")[0].firstChild
            if not isinstance(source, minidom.Text):
                continue
            translation = message.getElementsByTagName(
                "translation")[0].firstChild
            if isinstance(translation,
                          minidom.Text) and translation.data != "":
                if source.data == translation.data:
                    continue
                examples.append(
                    f"<source>{source.data}</source>\n"
                    f"<translation>{translation.data}</translation>\n")

    # random shuffle examples
    random.shuffle(examples)
    ai_prompt += "\n".join(examples[:30])

    ai_prompt += """```

Now, please translate all of the following 50 strings, try to be
creative and avoid making the translation the same as the source. Don't repeat
the example translations. Use a code block for all the translations. Please
preserve any newlines in the source strings when translating.

```
"""

    # 3. get all the source strings that have no translation and are type="unfinished".
    # Ask the AI to translate them.
    requests = []

    for context in dom.getElementsByTagName("context"):
        for message in context.getElementsByTagName("message"):
            source = message.getElementsByTagName("source")[0].firstChild
            if not isinstance(source, minidom.Text):
                continue
            translation = message.getElementsByTagName("translation")[0]
            if (not translation.firstChild or
                (isinstance(translation.firstChild, minidom.Text)
                 and not translation.firstChild.data)
                ) and translation.getAttribute("type") == "unfinished":
                requests.append(f"<source>{source.data}</source>\n")

    random.shuffle(requests)
    ai_prompt += "\n".join(requests[:50])
    ai_prompt += "```"

    # 4. send the prompt to the AI and get the response.
    send_ai_prompt(ai_prompt)


if __name__ == "__main__":
    main()
