import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from src.domain.rol_usuario import (
    RolUsuario
)

from src.gestion.base_datos import (
    obtener_sesion
)

from src.gestion.esquemas import (
    EstadoSenalActualizar,
    HistorialEstadoRespuesta,
    SenalRespuesta
)

from src.gestion.modelos import (
    ClaseSenalBD,
    UsuarioBD
)

from src.gestion.seguridad import (
    requerir_roles
)

from src.gestion.servicios.senales import (
    actualizar_estado_senal,
    listar_historial_senal,
    listar_senales
)


router = APIRouter(
    prefix="/senales",
    tags=["Señales"]
)


@router.get(
    "",
    response_model=list[SenalRespuesta]
)
def obtener_senales(
    sesion: Session = Depends(
        obtener_sesion
    ),

    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.OPERADOR,
            RolUsuario.ADMINISTRADOR
        )
    )
):

    resultados = listar_senales(
        sesion
    )

    return [
        SenalRespuesta(
            id=senal.id,

            clase_senal_id=(
                senal.clase_senal_id
            ),

            clase_nombre=(
                clase.nombre
            ),

            latitud=senal.latitud,
            longitud=senal.longitud,

            estado_actual=(
                senal.estado_actual
            ),

            fecha_creacion=(
                senal.fecha_creacion
            ),

            fecha_actualizacion=(
                senal.fecha_actualizacion
            )
        )

        for senal, clase in resultados
    ]

@router.patch(
    "/{senal_id}/estado",
    response_model=SenalRespuesta
)
@router.patch(
    "/{senal_id}/estado",
    response_model=SenalRespuesta
)
def cambiar_estado_senal(
    senal_id: uuid.UUID,
    datos: EstadoSenalActualizar,

    sesion: Session = Depends(
        obtener_sesion
    ),

    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.OPERADOR,
            RolUsuario.ADMINISTRADOR
        )
    )
):

    try:

        senal, historial = (
            actualizar_estado_senal(
                sesion=sesion,
                senal_id=senal_id,
                usuario_id=usuario.id,
                estado_nuevo=datos.estado,
                comentario=datos.comentario
            )
        )

    except LookupError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    clase = sesion.get(
        ClaseSenalBD,
        senal.clase_senal_id
    )

    return SenalRespuesta(
        id=senal.id,

        clase_senal_id=(
            senal.clase_senal_id
        ),

        clase_nombre=(
            clase.nombre
        ),

        latitud=senal.latitud,
        longitud=senal.longitud,

        estado_actual=(
            senal.estado_actual
        ),

        fecha_creacion=(
            senal.fecha_creacion
        ),

        fecha_actualizacion=(
            senal.fecha_actualizacion
        )
    )

@router.get(
    "/{senal_id}/historial",
    response_model=list[
        HistorialEstadoRespuesta
    ]
)
def obtener_historial_senal(
    senal_id: uuid.UUID,

    sesion: Session = Depends(
        obtener_sesion
    ),

    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.OPERADOR,
            RolUsuario.ADMINISTRADOR
        )
    )
):

    try:

        resultados = (
            listar_historial_senal(
                sesion=sesion,
                senal_id=senal_id
            )
        )

    except LookupError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    return [
        HistorialEstadoRespuesta(
            id=historial.id,

            senal_id=(
                historial.senal_id
            ),

            usuario_id=(
                historial.usuario_id
            ),

            nombre_usuario=(
                usuario_bd.nombre_usuario
            ),

            estado_anterior=(
                historial.estado_anterior
            ),

            estado_nuevo=(
                historial.estado_nuevo
            ),

            comentario=(
                historial.comentario
            ),

            fecha_cambio=(
                historial.fecha_cambio
            )
        )

        for historial, usuario_bd
        in resultados
    ]