"""Endpoints de sesión: login, logout y usuario actual."""

import datetime as dt

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.core.config import Settings
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutResponse, UserRead
from app.services import auth_service
from app.services.auth_service import AuthError

router = APIRouter(prefix="/auth", tags=["auth"])

# Los atributos deben coincidir con los usados al crear la cookie; de lo contrario
# el navegador no elimina la cookie original.
COOKIE_EXPIRED = dt.datetime(1970, 1, 1, tzinfo=dt.UTC)


def _status_for(error: AuthError) -> int:
    if isinstance(error, auth_service.InvalidCredentialsError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(error, auth_service.WeakPasswordError):
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_409_CONFLICT


def _cookie_attributes(settings: Settings) -> dict[str, object]:
    return {
        "key": settings.session_cookie_name,
        "httponly": True,
        "secure": settings.session_cookie_secure,
        "samesite": settings.session_cookie_samesite,
        "path": settings.session_cookie_path,
        "domain": settings.session_cookie_domain,
    }


@router.post("/login", response_model=UserRead)
async def login(
    payload: LoginRequest, response: Response, session: SessionDep, settings: SettingsDep
) -> User:
    try:
        user = await auth_service.authenticate(session, payload.email, payload.password)
    except AuthError as error:
        raise HTTPException(
            status_code=_status_for(error),
            detail={"code": error.code, "message": error.message},
        ) from None

    response.set_cookie(
        value=create_access_token(user.id),
        max_age=settings.access_token_expire_minutes * 60,
        **_cookie_attributes(settings),
    )
    return user


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response, settings: SettingsDep) -> LogoutResponse:
    # No se usa delete_cookie: su expires=0 se renderiza con la hora actual en
    # lugar del epoch, así que la caducidad se fija explícitamente.
    response.set_cookie(
        value="",
        max_age=0,
        expires=COOKIE_EXPIRED,
        **_cookie_attributes(settings),
    )
    return LogoutResponse(message="Sesión cerrada.")


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> User:
    return current_user
