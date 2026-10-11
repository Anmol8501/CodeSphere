"""The single place that maps CodeArena languages to Judge0.

Nothing else in the codebase may hardcode Judge0 language ids. To add a
language later (C, Go, Rust, ...): add it to ProgrammingLanguage, add an entry
here, and register its editor grammar in the frontend.
"""

from dataclasses import dataclass

from app.models.problem import ProgrammingLanguage


@dataclass(frozen=True)
class LanguageSpec:
    label: str
    # Judge0 CE 1.13.x language id.
    judge0_id: int
    judge0_name: str
    extension: str
    # Multiplier on the problem's time limit (JVM / interpreter start-up cost).
    time_factor: float = 1.0


LANGUAGES: dict[ProgrammingLanguage, LanguageSpec] = {
    ProgrammingLanguage.CPP: LanguageSpec("C++", 54, "C++ (GCC 9.2.0)", "cpp", 1.0),
    ProgrammingLanguage.JAVA: LanguageSpec("Java", 62, "Java (OpenJDK 13.0.1)", "java", 2.0),
    ProgrammingLanguage.PYTHON: LanguageSpec("Python", 71, "Python (3.8.1)", "py", 3.0),
}


def parse_language(value: object) -> ProgrammingLanguage | None:
    """"cpp" / "CPP" -> ProgrammingLanguage.CPP; anything unsupported -> None."""
    if not isinstance(value, str):
        return None
    try:
        language = ProgrammingLanguage(value.strip().upper())
    except ValueError:
        return None
    return language if language in LANGUAGES else None
