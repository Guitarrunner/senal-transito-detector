import bcrypt

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.gestion.modelos import UsuarioBD


def autenticar_usuario(
    sesion: Session,
    nombre_usuario: str,
    password: str
) -> UsuarioBD | None:

    usuario = sesion.scalar(
        select(UsuarioBD).where(
            UsuarioBD.nombre_usuario == nombre_usuario
        )
    )

    if usuario is None:
        return None

    if not usuario.activo:
        return None

    password_correcto = bcrypt.checkpw(
        password.encode("utf-8"),
        usuario.password_hash.encode("utf-8")
    )

    if not password_correcto:
        return None

    return usuario

