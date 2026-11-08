import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.domain.rol_usuario import RolUsuario
from src.gestion.base_datos import obtener_sesion
from src.gestion.esquemas import UsuarioGestionActualizar, UsuarioGestionCrear, UsuarioGestionRespuesta
from src.gestion.modelos import UsuarioBD
from src.gestion.seguridad import requerir_roles
from src.gestion.servicios.autenticacion import generar_hash


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=list[UsuarioGestionRespuesta])
def listar_usuarios(
    sesion: Session = Depends(obtener_sesion),
    _administrador: UsuarioBD = Depends(
        requerir_roles(RolUsuario.ADMINISTRADOR)
    ),
):
    consulta = select(
        UsuarioBD.id,
        UsuarioBD.nombre_usuario,
        UsuarioBD.rol,
        UsuarioBD.activo,
    ).order_by(UsuarioBD.nombre_usuario)

    return sesion.execute(consulta).mappings().all()

@router.post("", response_model=UsuarioGestionRespuesta, status_code=201)
def crear_usuario(
    datos: UsuarioGestionCrear,
    sesion: Session = Depends(obtener_sesion),
    _administrador: UsuarioBD = Depends(
        requerir_roles(RolUsuario.ADMINISTRADOR)
    ),
):
    nombre = datos.nombre_usuario.strip()
    password = datos.password.get_secret_value()

    if not 1 <= len(nombre) <= 50:
        raise HTTPException(422, "El usuario debe tener entre 1 y 50 caracteres.")

    if len(password) < 8:
        raise HTTPException(
            422,
            "La contraseña debe tener al menos 8 caracteres.",
        )

    usuario = UsuarioBD(
        nombre_usuario=nombre,
        password_hash=generar_hash(password),
        rol=datos.rol,
        activo=True,
    )
    sesion.add(usuario)

    try:
        sesion.commit()
    except IntegrityError as error:
        sesion.rollback()
        if getattr(error.orig, "sqlstate", None) == "23505":
            raise HTTPException(409, "Ese nombre de usuario ya existe.") from error
        raise

    return UsuarioGestionRespuesta(
        id=usuario.id,
        nombre_usuario=usuario.nombre_usuario,
        rol=usuario.rol,
        activo=usuario.activo,
    )

@router.patch("/{usuario_id}", response_model=UsuarioGestionRespuesta)
def actualizar_usuario(
    usuario_id: uuid.UUID,
    datos: UsuarioGestionActualizar,
    sesion: Session = Depends(obtener_sesion),
    administrador: UsuarioBD = Depends(
        requerir_roles(RolUsuario.ADMINISTRADOR)
    ),
):
    if usuario_id == administrador.id:
        raise HTTPException(409, "No podés modificar tu propia cuenta.")

    if datos.rol is None and datos.activo is None:
        raise HTTPException(422, "Indicá un rol o un estado para actualizar.")

    consulta = (
        select(UsuarioBD)
        .where(UsuarioBD.id.in_((administrador.id, usuario_id)))
        .order_by(UsuarioBD.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    cuentas = {
        cuenta.id: cuenta
        for cuenta in sesion.scalars(consulta)
    }

    cuenta_admin = cuentas.get(administrador.id)
    if (
        cuenta_admin is None
        or not cuenta_admin.activo
        or cuenta_admin.rol != RolUsuario.ADMINISTRADOR
    ):
        raise HTTPException(403, "Ya no tenés permisos de administrador.")

    usuario = cuentas.get(usuario_id)
    if usuario is None:
        raise HTTPException(404, "Usuario no encontrado.")

    if datos.rol is not None:
        usuario.rol = datos.rol

    if datos.activo is not None:
        usuario.activo = datos.activo

    respuesta = UsuarioGestionRespuesta(
        id=usuario.id,
        nombre_usuario=usuario.nombre_usuario,
        rol=usuario.rol,
        activo=usuario.activo,
    )
    sesion.commit()
    return respuesta

@router.delete("/{usuario_id}", status_code=204, response_class=Response)
def eliminar_usuario(
    usuario_id: uuid.UUID,
    sesion: Session = Depends(obtener_sesion),
    administrador: UsuarioBD = Depends(
        requerir_roles(RolUsuario.ADMINISTRADOR)
    ),
):
    administrador_id = administrador.id
    if usuario_id == administrador_id:
        raise HTTPException(409, "No podés eliminar tu propia cuenta.")

    consulta = (
        select(UsuarioBD)
        .where(UsuarioBD.id.in_((administrador_id, usuario_id)))
        .order_by(UsuarioBD.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    cuentas = {cuenta.id: cuenta for cuenta in sesion.scalars(consulta)}

    cuenta_admin = cuentas.get(administrador_id)
    if (
        cuenta_admin is None
        or not cuenta_admin.activo
        or cuenta_admin.rol != RolUsuario.ADMINISTRADOR
    ):
        raise HTTPException(403, "Ya no tenés permisos de administrador.")

    usuario = cuentas.get(usuario_id)
    if usuario is None:
        raise HTTPException(404, "Usuario no encontrado.")

    sesion.delete(usuario)
    try:
        sesion.commit()
    except IntegrityError as error:
        sesion.rollback()
        if getattr(error.orig, "sqlstate", None) == "23503":
            raise HTTPException(
                409,
                "La cuenta tiene registros asociados. Podés desactivarla.",
            ) from error
        raise

    return Response(status_code=204)