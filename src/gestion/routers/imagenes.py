import mimetypes
import os
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.domain.rol_usuario import RolUsuario
from src.gestion.base_datos import obtener_sesion
from src.gestion.esquemas import (
    AnotacionCrear,
    AnotacionRespuesta,
)
from src.gestion.modelos import (
    AnotacionBD,
    UsuarioBD,
)
from src.gestion.seguridad import requerir_roles
from src.gestion.servicios.imagenes import (
    crear_anotacion,
    eliminar_anotacion,
    listar_anotaciones,
    obtener_clase,
    obtener_imagen,
)

router = APIRouter(
    prefix="/imagenes",
    tags=["Imágenes y anotaciones"]
)

@router.get(
    "/{imagen_id}/archivo"
)
def obtener_archivo_imagen(
    imagen_id: uuid.UUID,
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    imagen = obtener_imagen(
        sesion,
        imagen_id
    )

    if imagen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada."
        )

    directorio_base = Path(
        os.getenv(
            "DATASET_STORAGE_DIR",
            "data/datasets"
        )
    ).resolve()

    ruta_archivo = (
        directorio_base
        / imagen.ruta_archivo
    ).resolve()

    if not ruta_archivo.is_relative_to(
        directorio_base
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ruta de archivo inválida."
        )

    if not ruta_archivo.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo físico no existe."
        )

    media_type, _ = mimetypes.guess_type(
        str(ruta_archivo)
    )

    return FileResponse(
        path=ruta_archivo,
        media_type=media_type
    )

@router.post(
    "/{imagen_id}/anotaciones",
    response_model=AnotacionRespuesta,
    status_code=status.HTTP_201_CREATED
)
def agregar_anotacion(
    imagen_id: uuid.UUID,
    datos: AnotacionCrear,
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    imagen = obtener_imagen(
        sesion,
        imagen_id
    )

    if imagen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada."
        )

    clase = obtener_clase(
        sesion,
        datos.clase_senal_id
    )

    if clase is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase de señal no encontrada."
        )

    if not clase.activa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clase seleccionada se encuentra inactiva."
        )

    try:
        anotacion = crear_anotacion(
            sesion=sesion,
            imagen=imagen,
            clase=clase,
            creado_por=usuario.id,
            bbox_x1=datos.bbox_x1,
            bbox_y1=datos.bbox_y1,
            bbox_x2=datos.bbox_x2,
            bbox_y2=datos.bbox_y2
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    return AnotacionRespuesta(
        id=anotacion.id,
        imagen_id=anotacion.imagen_id,

        clase_senal_id=clase.id,
        clase_codigo=clase.codigo,
        clase_nombre=clase.nombre,

        creado_por=anotacion.creado_por,

        bbox_x1=anotacion.bbox_x1,
        bbox_y1=anotacion.bbox_y1,
        bbox_x2=anotacion.bbox_x2,
        bbox_y2=anotacion.bbox_y2,

        fecha_creacion=anotacion.fecha_creacion
    )

@router.get(
    "/{imagen_id}/anotaciones",
    response_model=list[AnotacionRespuesta]
)
def obtener_anotaciones(
    imagen_id: uuid.UUID,
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    imagen = obtener_imagen(
        sesion,
        imagen_id
    )

    if imagen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada."
        )

    resultados = listar_anotaciones(
        sesion,
        imagen_id
    )

    return [
        AnotacionRespuesta(
            id=anotacion.id,
            imagen_id=anotacion.imagen_id,

            clase_senal_id=clase.id,
            clase_codigo=clase.codigo,
            clase_nombre=clase.nombre,

            creado_por=anotacion.creado_por,

            bbox_x1=anotacion.bbox_x1,
            bbox_y1=anotacion.bbox_y1,
            bbox_x2=anotacion.bbox_x2,
            bbox_y2=anotacion.bbox_y2,

            fecha_creacion=anotacion.fecha_creacion
        )
        for anotacion, clase in resultados
    ]

@router.delete(
    "/{imagen_id}/anotaciones/{anotacion_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def borrar_anotacion(
    imagen_id: uuid.UUID,
    anotacion_id: uuid.UUID,
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    anotacion = sesion.get(
        AnotacionBD,
        anotacion_id
    )

    if (
        anotacion is None
        or anotacion.imagen_id != imagen_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anotación no encontrada."
        )

    eliminar_anotacion(
        sesion,
        anotacion
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )