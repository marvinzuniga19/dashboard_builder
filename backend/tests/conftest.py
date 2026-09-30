"""Las pruebas nunca usan la base de datos de ejecución del proyecto.

Las variables de entorno se fijan antes de importar nada de ``app``: los módulos
de la aplicación crean el engine en el momento de importarse y ``get_settings``
cachea el resultado, por lo que un import prematuro apuntaría al ``.env`` real.
"""

import os
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.models.user import User

test_directory = TemporaryDirectory(prefix="dashboard-builder-tests-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_directory.name}/test.db"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
os.environ["JWT_SECRET_KEY"] = "clave-de-pruebas-que-no-se-usa-en-produccion-000000"


def pytest_sessionfinish() -> None:
    test_directory.cleanup()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    """El esquema de pruebas se genera con Alembic, nunca con create_all."""
    from alembic import command
    from alembic.config import Config

    from app.core.config import BACKEND_DIR, get_settings

    database_path = Path(str(get_settings().database_connection_url.database))
    if database_path.parent != Path(test_directory.name):
        pytest.fail(
            "La configuración se leyó antes de fijar DATABASE_URL: las pruebas "
            f"apuntarían a {database_path} en lugar del directorio temporal."
        )

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")


@pytest.fixture(autouse=True)
async def clean_users() -> Iterator[None]:
    from app.core.database import session_factory
    from app.models.user import User

    async with session_factory() as session:
        await session.execute(delete(User))
        await session.commit()
    yield


@pytest.fixture(name="client")
def client_fixture() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(name="session")
async def session_fixture() -> Iterator[AsyncSession]:
    """Sesión propia para preparar datos sin depender del estado de la API."""
    from app.core.database import session_factory

    async with session_factory() as session:
        yield session


@pytest.fixture(name="user")
async def user_fixture(session: AsyncSession) -> User:
    from app.services.auth_service import create_user

    return await create_user(session, "ana@example.com", "contrasena-segura", "Ana Ruiz")


@pytest.fixture(name="logged_in_client")
def logged_in_client_fixture(client: TestClient, user: User) -> TestClient:
    """Cliente con sesión iniciada por la propia API, como haría el navegador."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "contrasena-segura"},
    )
    assert response.status_code == 200
    return client
