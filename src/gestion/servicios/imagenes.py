import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.gestion.modelos import (
    AnotacionBD,
    ClaseSenalBD,
    ImagenDatasetBD,
)


def obtener_imagen(
    sesion: Session,
    imagen_id: uuid.UUID
) -> ImagenDatasetBD | None:

    return sesion.get(
        ImagenDatasetBD,
        imagen_id
    )


def obtener_clase(
    sesion: Session,
    clase_senal_id: int
) -> ClaseSenalBD | None:

    return sesion.get(
        ClaseSenalBD,
        clase_senal_id
    )


def validar_bbox(
    imagen: ImagenDatasetBD,
    bbox_x1: int,
    bbox_y1: int,
    bbox_x2: int,
    bbox_y2: int
):
    if bbox_x1 < 0 or bbox_y1 < 0:
        raise ValueError(
            "Las coordenadas iniciales no pueden ser negativas."
        )

    if bbox_x2 > imagen.ancho:
        raise ValueError(
            "La coordenada x2 excede el ancho de la imagen."
        )

    if bbox_y2 > imagen.alto:
        raise ValueError(
            "La coordenada y2 excede el alto de la imagen."
        )

    if bbox_x1 >= bbox_x2:
        raise ValueError(
            "bbox_x1 debe ser menor que bbox_x2."
        )

    if bbox_y1 >= bbox_y2:
        raise ValueError(
            "bbox_y1 debe ser menor que bbox_y2."
        )


def crear_anotacion(
    sesion: Session,
    imagen: ImagenDatasetBD,
    clase: ClaseSenalBD,
    creado_por: uuid.UUID,
    bbox_x1: int,
    bbox_y1: int,
    bbox_x2: int,
    bbox_y2: int
) -> AnotacionBD:

    validar_bbox(
        imagen,
        bbox_x1,
        bbox_y1,
        bbox_x2,
        bbox_y2
    )

    anotacion = AnotacionBD(
        imagen_id=imagen.id,
        clase_senal_id=clase.id,
        creado_por=creado_por,
        bbox_x1=bbox_x1,
        bbox_y1=bbox_y1,
        bbox_x2=bbox_x2,
        bbox_y2=bbox_y2
    )

    try:
        sesion.add(anotacion)
        sesion.commit()
        sesion.refresh(anotacion)

    except Exception:
        sesion.rollback()
        raise

    return anotacion


def listar_anotaciones(
    sesion: Session,
    imagen_id: uuid.UUID
):
    consulta = (
        select(
            AnotacionBD,
            ClaseSenalBD
        )
        .join(
            ClaseSenalBD,
            AnotacionBD.clase_senal_id
            == ClaseSenalBD.id
        )
        .where(
            AnotacionBD.imagen_id
            == imagen_id
        )
        .order_by(
            AnotacionBD.fecha_creacion
        )
    )

    return sesion.execute(
        consulta
    ).all()


def eliminar_anotacion(
    sesion: Session,
    anotacion: AnotacionBD
):
    try:
        sesion.delete(anotacion)
        sesion.commit()

    except Exception:
        sesion.rollback()
        raise