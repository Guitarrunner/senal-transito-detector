import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from src.domain.rol_usuario import RolUsuario
from src.gestion.base_datos import obtener_sesion
from src.gestion.modelos import UsuarioBD


load_dotenv()


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)
JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)


if JWT_SECRET_KEY is None:
    raise RuntimeError(
        "No se encontró JWT_SECRET_KEY en las variables de entorno."
    )


bearer = HTTPBearer(
    auto_error=False
)


def crear_access_token(
    usuario_id: uuid.UUID
) -> str:

    ahora = datetime.now(timezone.utc)

    expiracion = ahora + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": expiracion
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer),
    sesion: Session = Depends(obtener_sesion)
) -> UsuarioBD:

    error_credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado.",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    if credenciales is None:
        raise error_credenciales

    try:
        payload = jwt.decode(
            credenciales.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        usuario_id_texto = payload.get("sub")

        if usuario_id_texto is None:
            raise error_credenciales

        usuario_id = uuid.UUID(
            usuario_id_texto
        )

    except (
        InvalidTokenError,
        ValueError
    ):
        raise error_credenciales

    usuario = sesion.get(
        UsuarioBD,
        usuario_id
    )

    if usuario is None:
        raise error_credenciales

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra inactivo."
        )

    return usuario


def requerir_roles(
    *roles_permitidos: RolUsuario
):

    def verificar_rol(
        usuario: UsuarioBD = Depends(
            obtener_usuario_actual
        )
    ) -> UsuarioBD:

        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción."
            )

        return usuario

    return verificar_rol