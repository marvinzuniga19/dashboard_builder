"""Hashing de contraseñas y tokens de sesión.

El token viaja en una cookie httpOnly (§9 del AGENTS); nunca en el cuerpo de la
respuesta ni en localStorage. El claim ``sub`` contiene el identificador del
usuario y ``type`` permite invalidar el token si en el futuro se añaden otros
tipos de credencial.
"""

import datetime as dt

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

TOKEN_TYPE = "access"
BCRYPT_ROUNDS = 12

pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=BCRYPT_ROUNDS
)


class InvalidTokenError(ValueError):
    """El token no es utilizable: alterado, expirado o firmado con otra clave."""


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        # Hash con formato desconocido: se trata como credencial inválida.
        return False


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    issued_at = dt.datetime.now(dt.UTC)
    expires_at = issued_at + dt.timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": TOKEN_TYPE,
            "iat": issued_at,
            "exp": expires_at,
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> int:
    """Devuelve el identificador del usuario o lanza ``InvalidTokenError``."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as error:
        raise InvalidTokenError("El token de sesión no es válido.") from error

    if payload.get("type") != TOKEN_TYPE:
        raise InvalidTokenError("El token no corresponde a una sesión.")

    subject = payload.get("sub")
    try:
        return int(subject)
    except (TypeError, ValueError) as error:
        raise InvalidTokenError("El token no identifica a un usuario.") from error
