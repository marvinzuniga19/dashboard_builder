"""Pruebas del alta local de usuarios: python -m app.cli.create_user."""

import pytest
from fastapi.testclient import TestClient

from app.cli import create_user as cli

PASSWORD = "contrasena-segura"


def answer_with(monkeypatch: pytest.MonkeyPatch, *answers: str) -> None:
    replies = iter(answers)
    monkeypatch.setattr(cli.getpass, "getpass", lambda *_args, **_kwargs: next(replies))


def test_cli_creates_a_usable_user(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
    capsys: pytest.CaptureFixture[str],
) -> None:
    answer_with(monkeypatch, PASSWORD, PASSWORD)
    assert cli.main(["--email", "Luis@Example.com", "--full-name", "Luis Pérez"]) == 0
    assert "luis@example.com" in capsys.readouterr().out

    # El usuario creado por el CLI debe poder iniciar sesión en la API.
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "luis@example.com", "password": PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Luis Pérez"


def test_cli_requires_matching_passwords(monkeypatch: pytest.MonkeyPatch) -> None:
    answer_with(monkeypatch, PASSWORD, "otra-contrasena")
    with pytest.raises(SystemExit):
        cli.main(["--email", "luis@example.com"])


def test_cli_rejects_weak_passwords(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answer_with(monkeypatch, "corta", "corta")
    assert cli.main(["--email", "luis@example.com"]) == 1
    assert "entre 8 y 72" in capsys.readouterr().err


def test_cli_reports_duplicate_email(
    monkeypatch: pytest.MonkeyPatch, user: object, capsys: pytest.CaptureFixture[str]
) -> None:
    answer_with(monkeypatch, PASSWORD, PASSWORD)
    assert cli.main(["--email", "ANA@example.com"]) == 1
    assert "Ya existe un usuario" in capsys.readouterr().err


def test_cli_requires_an_email_argument() -> None:
    with pytest.raises(SystemExit):
        cli.main([])
