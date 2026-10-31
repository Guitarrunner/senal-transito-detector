from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.gestion.base_datos import obtener_sesion
from src.gestion.esquemas import (
    LoginEntrada,
    LoginRespuesta,
    UsuarioAutenticadoRespuesta,
)
from src.gestion.modelos import UsuarioBD
from src.gestion.seguridad import (
    crear_access_token,
    obtener_usuario_actual,
)
from src.gestion.servicios.autenticacion import autenticar_usuario

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


@router.post(
    "/login",
    response_model=LoginRespuesta
)
def login(
    datos: LoginEntrada,
    sesion: Session = Depends(obtener_sesion)
):
    usuario = autenticar_usuario(
        sesion,
        datos.nombre_usuario,
        datos.password
    )

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos."
        )

    access_token = crear_access_token(
        usuario.id
    )

    return LoginRespuesta(
        access_token=access_token,
        token_type="bearer",
        usuario=UsuarioAutenticadoRespuesta(
            id=usuario.id,
            nombre_usuario=usuario.nombre_usuario,
            rol=usuario.rol
        )
    )

@router.get(
    "/me",
    response_model=UsuarioAutenticadoRespuesta
)

def obtener_mi_usuario(
    usuario: UsuarioBD = Depends(
        obtener_usuario_actual
    )
):
    return UsuarioAutenticadoRespuesta(
        id=usuario.id,
        nombre_usuario=usuario.nombre_usuario,
        rol=usuario.rol
    )