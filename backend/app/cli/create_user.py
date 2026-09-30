"""Alta local de usuarios. No existe endpoint público de registro (§35, FASE 2).

Uso:

    python -m app.cli.create_user --email admin@example.com --full-name "Ada Lovelace"

La contraseña se solicita de forma interactiva: pasarla como argumento la
dejaría en el historial del shell.
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy.exc import OperationalError

from app.core.database import engine, session_factory
from app.services.auth_service import (
    AuthError,
    create_user,
    normalize_email,
    validate_password_strength,
)


def read_password() -> str:
    password = getpass.getpass("Contraseña: ")
    confirmation = getpass.getpass("Repite la contraseña: ")
    if password != confirmation:
        raise SystemExit("Las contraseñas no coinciden.")
    return password


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli.create_user",
        description="Crea un usuario en la base de datos de Dashboard Builder.",
    )
    parser.add_argument("--email", required=True, help="Correo del usuario.")
    parser.add_argument("--full-name", default=None, help="Nombre visible (opcional).")
    return parser.parse_args(argv)


async def run_creation(email: str, password: str, full_name: str | None) -> int:
    try:
        async with session_factory() as session:
            user = await create_user(session, email, password, full_name)
    finally:
        await engine.dispose()
    return user.id


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    email = normalize_email(arguments.email)
    password = read_password()
    try:
        validate_password_strength(password)
    except AuthError as error:
        print(error.message, file=sys.stderr)
        return 1

    try:
        user_id = asyncio.run(run_creation(email, password, arguments.full_name))
    except AuthError as error:
        print(error.message, file=sys.stderr)
        return 1
    except OperationalError:
        print(
            "No se pudo conectar con la base de datos. Ejecuta 'alembic upgrade head' "
            "y revisa DATABASE_URL.",
            file=sys.stderr,
        )
        return 1

    print(f"Usuario creado correctamente con id {user_id} y correo {email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
