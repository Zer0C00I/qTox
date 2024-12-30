# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 The TokTok team
from typing import Any
from typing import Optional


class UserAbort(Exception):
    pass


class InvalidState(Exception):
    pass


def print_stage_start(name: str, description: str) -> None:
    """Prints a colorful message indicating that a stage is starting.

    Does not print a newline at the end.

    Looks roughly like:
       [ .... ] Stage name (requirement description)
    """
    print(f"\033[1;34m[ .... ]\033[0m {name} {description}",
          end="",
          flush=True)


def print_stage_end(name: str, description: str, success: bool) -> None:
    """Prints a colorful message indicating that a stage has finished.

    Now (unlike the above print_stage_start) it prints a newline at the end to
    get ready for the next stage.

    Looks roughly like:
       [  OK  ] Stage name (result description)
    """
    status = " \033[1;32mOK\033[0m " if success else "\033[1;31mFAIL\033[0m"
    print(f"\r\033[1;34m[ {status} \033[1;34m]\033[0m {name} {description}")


def padded(text: str, length: int) -> str:
    """Pads the text with spaces to the given length."""
    return f"{text}{' ' * (length - len(text))}"


class Stage:
    """A class to run stages and print colorful messages for the user."""

    def __init__(self,
                 name: str,
                 description: str,
                 failures: Optional[list[str]] = None) -> None:
        """Initializes a new stage. Doesn't enter it yet (use `with` for that).

        The `failures` parameter is a list that will be appended to if the stage
        fails. If it's None, the stage will raise an exception on error instead.
        """
        self.failures = failures
        self.name = name
        self.description = f"({description})"
        self.done = False

    def __enter__(self) -> "Stage":
        print_stage_start(self.name, self.description)
        return self

    def ok(self, description: str = "Done") -> None:
        print_stage_end(
            self.name,
            padded(f"({description})", len(self.description)),
            True,
        )
        self.done = True

    def fail(self, description: str) -> None:
        print_stage_end(
            self.name,
            padded(f"({description})", len(self.description)),
            False,
        )
        if self.failures is not None:
            self.failures.append(self.name)
        else:
            raise InvalidState(f"Stage {self.name} failed: {description}")
        self.done = True

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if not self.done:
            self.fail("The stage did not complete")
