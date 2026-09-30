"""Dependencias reutilizables de las rutas.

``get_current_user`` resuelve la cookie httpOnly a un usuario activo. La cookie es
el único transporte aceptado (§9 del AGENTS): no se admiten tokens en cabeceras
``Authorization`` ni en el cuerpo, para no exponerlos a JavaScript.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import InvalidTokenError, decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "AUTH_REQUIRED", "message": message},
        headers={"WWW-Authenticate": "Cookie"},
    )


async def get_current_user(request: Request, session: SessionDep, settings: SettingsDep) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise _unauthorized("Inicia sesión para continuar.")

    try:
        user_id = decode_access_token(token)
    except InvalidTokenError:
        raise _unauthorized("Tu sesión no es válida o ha expirado.") from None

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Tu sesión ya no está autorizada.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
