"""Pruebas de la FASE 2: hashing, tokens, cookie de sesión y protección de endpoints."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.services.auth_service import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    WeakPasswordError,
    authenticate,
    create_user,
    normalize_email,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

COOKIE_NAME = get_settings().session_cookie_name
VALID_PASSWORD = "contrasena-segura"


def build_token(secret: str, expires_at: dt.datetime, subject: str = "1") -> str:
    return jwt.encode(
        {"sub": subject, "type": "access", "exp": expires_at},
        secret,
        algorithm="HS256",
    )


# --- Hashing de contraseñas ---


def test_hash_is_not_reversible_and_verifies() -> None:
    hashed = hash_password(VALID_PASSWORD)
    assert hashed != VALID_PASSWORD
    assert "contrasena-segura" not in hashed
    assert hashed.startswith("$2b$")
    assert verify_password(VALID_PASSWORD, hashed)
    assert not verify_password("otra-contrasena", hashed)


def test_same_password_produces_different_hashes() -> None:
    assert hash_password(VALID_PASSWORD) != hash_password(VALID_PASSWORD)


def test_verify_returns_false_for_corrupted_hash() -> None:
    assert not verify_password(VALID_PASSWORD, "no-es-un-hash")


# --- Tokens ---


def test_token_round_trip() -> None:
    assert decode_access_token(create_access_token(42)) == 42


def test_token_rejects_tampered_payload() -> None:
    token = create_access_token(1)
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload[:-2]}AA.{signature}"
    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_token_rejects_foreign_signature() -> None:
    token = build_token("otra-clave-que-no-deberia-firmar-nada-000000", dt.datetime.now(dt.UTC) + dt.timedelta(minutes=5))
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_rejects_expired() -> None:
    token = build_token(
        get_settings().jwt_secret_key.get_secret_value(),
        dt.datetime.now(dt.UTC) - dt.timedelta(minutes=1),
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_rejects_non_numeric_subject() -> None:
    token = build_token(
        get_settings().jwt_secret_key.get_secret_value(),
        dt.datetime.now(dt.UTC) + dt.timedelta(minutes=5),
        subject="no-es-un-id",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


# --- Servicio de usuarios ---


async def test_create_user_normalizes_email(session: AsyncSession) -> None:
    user = await create_user(session, "  Ana.Ruiz@Example.COM ", VALID_PASSWORD)
    assert user.email == "ana.ruiz@example.com"
    assert user.is_active is True


async def test_create_user_rejects_duplicates(session: AsyncSession) -> None:
    await create_user(session, "ana@example.com", VALID_PASSWORD)
    with pytest.raises(UserAlreadyExistsError):
        await create_user(session, "ANA@example.com", VALID_PASSWORD)


@pytest.mark.parametrize("password", ["corta", "x" * 73])
async def test_create_user_rejects_weak_passwords(session: AsyncSession, password: str) -> None:
    with pytest.raises(WeakPasswordError):
        await create_user(session, "ana@example.com", password)


async def test_password_is_stored_hashed(session: AsyncSession, user: User) -> None:
    assert user.hashed_password != VALID_PASSWORD
    assert verify_password(VALID_PASSWORD, user.hashed_password)


async def test_normalize_email_trims_and_lowercases() -> None:
    assert normalize_email("  Ana.Ruiz@Example.COM ") == "ana.ruiz@example.com"


# --- Endpoint de login ---


def test_login_succeeds_and_sets_http_only_cookie(client: TestClient, user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": VALID_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["email"] == "ana@example.com"
    assert body["full_name"] == "Ana Ruiz"
    assert body["is_active"] is True

    set_cookie = response.headers["set-cookie"]
    assert COOKIE_NAME in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie.replace("samesite", "SameSite")
    assert "Path=/" in set_cookie
    assert "Secure" not in set_cookie


def test_login_never_returns_the_password_hash(client: TestClient, user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": VALID_PASSWORD},
    )
    assert "hashed_password" not in response.text
    assert VALID_PASSWORD not in response.text


def test_login_accepts_email_in_any_case(client: TestClient, user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "  ANA@Example.com ", "password": VALID_PASSWORD},
    )
    assert response.status_code == 200


def test_login_rejects_wrong_password(client: TestClient, user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "contrasena-equivocada"},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_INVALID_CREDENTIALS"
    assert COOKIE_NAME not in response.cookies


def test_login_does_not_reveal_whether_the_email_exists(client: TestClient, user: User) -> None:
    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nadie@example.com", "password": VALID_PASSWORD},
    )
    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "contrasena-equivocada"},
    )
    assert unknown.status_code == wrong_password.status_code == 401
    assert unknown.json() == wrong_password.json()


async def test_login_rejects_inactive_user(
    client: TestClient, session: AsyncSession, user: User
) -> None:
    user.is_active = False
    await session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": VALID_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_login_validates_payload_shape(client: TestClient, user: User) -> None:
    response = client.post("/api/v1/auth/login", json={"email": "no-es-un-correo", "password": "x"})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


# --- Endpoint /auth/me ---


def test_me_requires_a_session(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_REQUIRED"


def test_me_returns_the_authenticated_user(
    logged_in_client: TestClient, user: User
) -> None:
    response = logged_in_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


def test_me_rejects_a_tampered_cookie(logged_in_client: TestClient) -> None:
    logged_in_client.cookies.set(
        COOKIE_NAME, f"{logged_in_client.cookies.get(COOKIE_NAME)}alterado"
    )
    response = logged_in_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_REQUIRED"


async def test_me_rejects_a_session_for_a_deleted_user(
    logged_in_client: TestClient, session: AsyncSession, user: User
) -> None:
    user.is_active = False
    await session.commit()

    response = logged_in_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_rejects_token_in_authorization_header(client: TestClient, user: User) -> None:
    """La cookie es el único transporte: la cabecera Authorization no habilita sesión."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    assert response.status_code == 401


# --- Endpoint /auth/logout ---


def test_logout_clears_the_session_cookie(logged_in_client: TestClient) -> None:
    assert logged_in_client.get("/api/v1/auth/me").status_code == 200

    response = logged_in_client.post("/api/v1/auth/logout")
    assert response.status_code == 200

    set_cookie = response.headers["set-cookie"]
    assert f"{COOKIE_NAME}=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "1970" in set_cookie
    assert logged_in_client.get("/api/v1/auth/me").status_code == 401


# --- Servicio de autenticación ---


async def test_authenticate_returns_user(session: AsyncSession, user: User) -> None:
    authenticated = await authenticate(session, "ANA@example.com", VALID_PASSWORD)
    assert authenticated.id == user.id


async def test_authenticate_rejects_wrong_password(session: AsyncSession, user: User) -> None:
    with pytest.raises(InvalidCredentialsError):
        await authenticate(session, "ana@example.com", "otra-contrasena")
