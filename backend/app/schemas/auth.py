from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.user import UserOut
from app.schemas.validators import validate_full_name, validate_password_strength


class RegisterRequest(BaseModel):
    """Public student registration. There is intentionally no `role` field:
    every public registration becomes a STUDENT on the server. Unknown fields
    (e.g. a smuggled "role": "ADMIN") are rejected with 422."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(examples=["Asha Kumar"])
    email: EmailStr = Field(examples=["asha@college.edu"])
    password: str = Field(examples=["StrongPass123"])
    confirm_password: str = Field(examples=["StrongPass123"])

    @field_validator("full_name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        return validate_full_name(value)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def _passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


LoginPortal = Literal["STUDENT", "STAFF", "ADMIN"]


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["asha@college.edu"])
    password: str = Field(min_length=1, max_length=128)
    # Which login screen was used. This is only a UX hint: the server compares it
    # against the role stored in the database and rejects mismatches.
    portal: LoginPortal | None = Field(default=None, examples=["STUDENT"])


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
