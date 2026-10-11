"""Assembles the program that is sent to the judge.

Function-style problems ("implement class Solution") have a hidden driver per
language: a complete program containing the marker line below. The student's
code replaces the marker; the driver reads stdin, calls the student's method
and prints the result. Problems without a driver run the student's code as a
full program that reads stdin itself.
"""

USER_CODE_MARKER = "{{USER_CODE}}"


class HarnessError(ValueError):
    pass


def validate_driver(driver_code: str) -> None:
    if driver_code.count(USER_CODE_MARKER) != 1:
        raise HarnessError(f"The driver must contain {USER_CODE_MARKER} exactly once.")


def build_program(user_code: str, driver_code: str | None) -> str:
    if not driver_code:
        return user_code
    validate_driver(driver_code)
    before, after = driver_code.split(USER_CODE_MARKER)
    # Keep the driver's own line break after the marker; add one only if missing.
    separator = "" if after.startswith("\n") else "\n"
    return f"{before}{user_code.rstrip()}{separator}{after}"
