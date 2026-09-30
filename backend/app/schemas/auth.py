"""Contratos HTTP de autenticación."""

import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr, Field

MINIMUM_PASSWORD_LENGTH = 8
# bcrypt sólo considera los primeros 72 bytes: se rechazan contraseñas más largas
# en lugar de aceptarlas y descartar parte del secreto en silencio.
MAXIMUM_PASSWORD_LENGTH = 72


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MINIMUM_PASSWORD_LENGTH, max_length=MAXIMUM_PASSWORD_LENGTH)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None
    is_active: bool
    created_at: dt.datetime


class LogoutResponse(BaseModel):
    message: str
