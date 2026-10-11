"""Output comparison. The backend alone decides whether an output is correct.

Kept isolated so smarter checkers (floating point tolerance, unordered
output, special judges) can be added per problem later.
"""


def normalize_output(text: str) -> str:
    """Normalize only what never carries meaning in judged output.

    * Windows / old Mac line endings become "\\n".
    * Trailing spaces and tabs at the end of each line are removed.
    * Trailing blank lines (including the final newline) are removed.

    Leading spaces, spaces between tokens and blank lines in the middle are
    kept: they can be meaningful (e.g. printed patterns).
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip(" \t") for line in lines]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def outputs_match(actual: str, expected: str) -> bool:
    return normalize_output(actual) == normalize_output(expected)
