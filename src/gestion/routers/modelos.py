import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from src.domain.rol_usuario import (
    RolUsuario
)
from src.gestion.base_datos import (
    obtener_sesion
)
from src.gestion.esquemas import (
    EntrenamientoModeloCrear,
    EntrenamientoModeloRespuesta,
    VersionModeloRespuesta,
)
from src.gestion.modelos import (
    UsuarioBD
)
from src.gestion.seguridad import (
    requerir_roles
)
from src.gestion.servicios.entrenamiento_modelo import (
    crear_entrenamiento,
    iniciar_proceso_entrenamiento,
    listar_entrenamientos,
    obtener_entrenamiento,
)

from src.gestion.servicios.modelo import (
    listar_modelos,
    activar_modelo,
)


router = APIRouter(
    prefix="/modelos",
    tags=["Modelos"]
)


def _crear_respuesta(
    entrenamiento
):
    return EntrenamientoModeloRespuesta(
        id=entrenamiento.id,
        dataset_id=entrenamiento.dataset_id,
        creado_por=entrenamiento.creado_por,

        version=entrenamiento.version,
        modelo_base=entrenamiento.modelo_base,

        epocas=entrenamiento.epocas,
        imgsz=entrenamiento.imgsz,
        batch=entrenamiento.batch,

        estado=entrenamiento.estado,
        epoca_actual=(
            entrenamiento.epoca_actual
        ),

        mensaje_error=(
            entrenamiento.mensaje_error
        ),

        fecha_creacion=(
            entrenamiento.fecha_creacion
        ),

        fecha_inicio=(
            entrenamiento.fecha_inicio
        ),

        fecha_fin=(
            entrenamiento.fecha_fin
        ),

        version_modelo_id=(
            entrenamiento.version_modelo_id
        )
    )


@router.post(
    "/entrenamientos",
    response_model=(
        EntrenamientoModeloRespuesta
    ),
    status_code=status.HTTP_202_ACCEPTED
)
def iniciar_entrenamiento(
    datos: EntrenamientoModeloCrear,
    sesion: Session = Depends(
        obtener_sesion
    ),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    try:
        entrenamiento = (
            crear_entrenamiento(
                sesion=sesion,
                dataset_id=(
                    datos.dataset_id
                ),
                creado_por=usuario.id,
                version=datos.version,
                modelo_base=(
                    datos.modelo_base
                ),
                epocas=datos.epocas,
                imgsz=datos.imgsz,
                batch=datos.batch
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error)
        )

    iniciar_proceso_entrenamiento(
        entrenamiento.id
    )

    return _crear_respuesta(
        entrenamiento
    )


@router.get(
    "/entrenamientos",
    response_model=list[
        EntrenamientoModeloRespuesta
    ]
)
def obtener_entrenamientos(
    sesion: Session = Depends(
        obtener_sesion
    ),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    entrenamientos = (
        listar_entrenamientos(
            sesion
        )
    )

    return [
        _crear_respuesta(
            entrenamiento
        )
        for entrenamiento
        in entrenamientos
    ]


@router.get(
    "/entrenamientos/{entrenamiento_id}",
    response_model=(
        EntrenamientoModeloRespuesta
    )
)
def consultar_entrenamiento(
    entrenamiento_id: uuid.UUID,
    sesion: Session = Depends(
        obtener_sesion
    ),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    entrenamiento = (
        obtener_entrenamiento(
            sesion,
            entrenamiento_id
        )
    )

    if entrenamiento is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Entrenamiento no encontrado."
            )
        )

    return _crear_respuesta(
        entrenamiento
    )

@router.get(
    "",
    response_model=list[
        VersionModeloRespuesta
    ]
)
def obtener_modelos(
    sesion: Session = Depends(
        obtener_sesion
    ),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    modelos = listar_modelos(
        sesion
    )

    return [
        VersionModeloRespuesta(
            id=modelo.id,
            dataset_id=modelo.dataset_id,

            version=modelo.version,
            ruta_modelo=modelo.ruta_modelo,

            precision=modelo.precision,
            recall=modelo.recall,

            map_50=modelo.map_50,
            map_50_95=modelo.map_50_95,

            latencia_promedio_ms=(
                modelo.latencia_promedio_ms
            ),

            fps=modelo.fps,

            activo=modelo.activo,

            fecha_entrenamiento=(
                modelo.fecha_entrenamiento
            )
        )
        for modelo in modelos
    ]


@router.post(
    "/{modelo_id}/activar",
    response_model=VersionModeloRespuesta
)
def activar_version_modelo(
    modelo_id: uuid.UUID,
    sesion: Session = Depends(
        obtener_sesion
    ),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    try:
        modelo = activar_modelo(
            sesion,
            modelo_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error)
        )

    return VersionModeloRespuesta(
        id=modelo.id,
        dataset_id=modelo.dataset_id,

        version=modelo.version,
        ruta_modelo=modelo.ruta_modelo,

        precision=modelo.precision,
        recall=modelo.recall,

        map_50=modelo.map_50,
        map_50_95=modelo.map_50_95,

        latencia_promedio_ms=(
            modelo.latencia_promedio_ms
        ),

        fps=modelo.fps,

        activo=modelo.activo,

        fecha_entrenamiento=(
            modelo.fecha_entrenamiento
        )
    )