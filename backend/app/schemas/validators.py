"""Reusable field validators shared by request schemas."""

import re

from app.core.security import BCRYPT_MAX_BYTES

PASSWORD_MIN_LENGTH = 8


def validate_password_strength(password: str) -> str:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.")
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError("Password is too long (maximum 72 characters).")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("Password must contain at least one letter and one number.")
    return password


def validate_full_name(name: str) -> str:
    name = " ".join(name.split())  # trim + collapse inner whitespace
    if not name:
        raise ValueError("Full name is required.")
    if len(name) < 2:
        raise ValueError("Full name must be at least 2 characters long.")
    if len(name) > 120:
        raise ValueError("Full name must be at most 120 characters long.")
    return name
