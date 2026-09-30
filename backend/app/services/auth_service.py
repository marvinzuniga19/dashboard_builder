"""Reglas de negocio de acceso y alta de usuarios."""

from functools import cache

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import MAXIMUM_PASSWORD_LENGTH, MINIMUM_PASSWORD_LENGTH

INVALID_CREDENTIALS_MESSAGE = "El correo o la contraseña no son correctos."


@cache
def _dummy_hash() -> str:
    """Hash de un valor imposible: iguala el tiempo de respuesta cuando el correo
    no existe y evita enumerar cuentas por diferencia de latencia. Se calcula de
    forma diferida para no pagar bcrypt en el arranque."""
    return hash_password("contraseña-inexistente-para-igualar-tiempos")


class AuthError(Exception):
    """Error de dominio con código estable para la respuesta HTTP."""

    code = "AUTH_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidCredentialsError(AuthError):
    code = "AUTH_INVALID_CREDENTIALS"


class UserAlreadyExistsError(AuthError):
    code = "USER_EMAIL_TAKEN"


class WeakPasswordError(AuthError):
    code = "AUTH_WEAK_PASSWORD"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_password_strength(password: str) -> None:
    if not MINIMUM_PASSWORD_LENGTH <= len(password) <= MAXIMUM_PASSWORD_LENGTH:
        raise WeakPasswordError(
            f"La contraseña debe tener entre {MINIMUM_PASSWORD_LENGTH} y "
            f"{MAXIMUM_PASSWORD_LENGTH} caracteres."
        )


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    repository = UserRepository(session)
    user = await repository.get_by_email(normalize_email(email))
    if user is None:
        verify_password(password, _dummy_hash())
        raise InvalidCredentialsError(INVALID_CREDENTIALS_MESSAGE)
    if not verify_password(password, user.hashed_password) or not user.is_active:
        # Un usuario desactivado responde igual que uno con contraseña incorrecta:
        # la respuesta no debe revelar qué cuentas existen.
        raise InvalidCredentialsError(INVALID_CREDENTIALS_MESSAGE)
    return user


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    normalized_email = normalize_email(email)
    validate_password_strength(password)
    repository = UserRepository(session)
    if await repository.get_by_email(normalized_email) is not None:
        raise UserAlreadyExistsError("Ya existe un usuario con ese correo.")

    user = User(
        email=normalized_email,
        full_name=full_name.strip() if full_name else None,
        hashed_password=hash_password(password),
    )
    try:
        return await repository.add(user)
    except IntegrityError:
        # Dos altas simultáneas con el mismo correo: la restricción única decide.
        await session.rollback()
        raise UserAlreadyExistsError("Ya existe un usuario con ese correo.") from None
