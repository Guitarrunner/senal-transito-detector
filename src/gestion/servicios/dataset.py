import os
import uuid

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from src.gestion.modelos import (
    DatasetBD,
    ImagenDatasetBD,
    AnotacionBD,
    ClaseSenalBD
)

register_heif_opener()

def crear_dataset(
    sesion: Session,
    nombre: str,
    descripcion: str | None,
    creado_por: uuid.UUID
) -> DatasetBD:

    dataset = DatasetBD(
        nombre=nombre,
        descripcion=descripcion,
        creado_por=creado_por
    )

    try:
        sesion.add(dataset)
        sesion.commit()
        sesion.refresh(dataset)

    except Exception:
        sesion.rollback()
        raise

    return dataset


def listar_datasets(
    sesion: Session
) -> list[DatasetBD]:

    consulta = (
        select(DatasetBD)
        .order_by(
            DatasetBD.fecha_creacion.desc()
        )
    )

    return list(
        sesion.scalars(consulta).all()
    )

def obtener_dataset(
    sesion: Session,
    dataset_id: uuid.UUID
) -> DatasetBD | None:

    return sesion.get(
        DatasetBD,
        dataset_id
    )

def guardar_imagen_dataset(
    sesion: Session,
    dataset: DatasetBD,
    nombre_original: str,
    contenido: bytes,
    grupo_fisico: str | None = None
) -> ImagenDatasetBD:

    if not contenido:
        raise ValueError(
            "El archivo de imagen está vacío."
        )

    try:
        with Image.open(BytesIO(contenido)) as imagen:
            imagen.verify()

        with Image.open(BytesIO(contenido)) as imagen:
            ancho, alto = imagen.size
            formato = imagen.format

    except (UnidentifiedImageError, OSError):
        raise ValueError(
            "El archivo proporcionado no es una imagen válida."
        )

    extensiones = {
        "JPEG": ".jpg",
        "PNG": ".png",
        "BMP": ".bmp",
        "HEIF": ".jpg"
    }

    if formato not in extensiones:
        raise ValueError(
            "Formato no permitido. Utilice JPG, PNG o BMP."
        )

    extension = extensiones[formato]

    directorio_base = Path(
        os.getenv(
            "DATASET_STORAGE_DIR",
            "data/datasets"
        )
    )

    directorio_dataset = (
        directorio_base / str(dataset.id)
    )

    directorio_dataset.mkdir(
        parents=True,
        exist_ok=True
    )

    nombre_fisico = f"{uuid.uuid4()}{extension}"
    ruta_fisica = directorio_dataset / nombre_fisico
    ruta_relativa = Path(str(dataset.id)) / nombre_fisico

    if formato == "HEIF":
        with Image.open(BytesIO(contenido)) as imagen:
            imagen.convert("RGB").save(
                ruta_fisica,
                format="JPEG",
                quality=95
            )
    else:
        ruta_fisica.write_bytes(contenido)
        
    imagen_bd = ImagenDatasetBD(
        dataset_id=dataset.id,
        ruta_archivo=str(ruta_relativa),
        nombre_archivo=nombre_original,
        ancho=ancho,
        alto=alto,
        conjunto=None,
        grupo_fisico=grupo_fisico,
        evidencia_id=None
    )

    try:
        sesion.add(imagen_bd)
        sesion.commit()
        sesion.refresh(imagen_bd)

    except Exception:
        sesion.rollback()

        if ruta_fisica.exists():
            ruta_fisica.unlink()

        raise

    return imagen_bd


def listar_imagenes_dataset(
    sesion: Session,
    dataset_id: uuid.UUID
) -> list[ImagenDatasetBD]:

    consulta = (
        select(ImagenDatasetBD)
        .where(
            ImagenDatasetBD.dataset_id
            == dataset_id
        )
        .order_by(
            ImagenDatasetBD.fecha_agregada
        )
    )

    return list(
        sesion.scalars(consulta).all()
    )

def obtener_estadisticas_anotaciones(
    sesion: Session,
    dataset_id: uuid.UUID
):
    conteos = (
        select(
            AnotacionBD.clase_senal_id.label(
                "clase_senal_id"
            ),
            func.count(
                func.distinct(
                    AnotacionBD.imagen_id
                )
            ).label(
                "imagenes_con_clase"
            ),
            func.count(
                AnotacionBD.id
            ).label(
                "cantidad_anotaciones"
            )
        )
        .join(
            ImagenDatasetBD,
            ImagenDatasetBD.id
            == AnotacionBD.imagen_id
        )
        .where(
            ImagenDatasetBD.dataset_id
            == dataset_id
        )
        .group_by(
            AnotacionBD.clase_senal_id
        )
        .subquery()
    )

    consulta = (
        select(
            ClaseSenalBD.id.label(
                "clase_senal_id"
            ),
            ClaseSenalBD.codigo.label(
                "clase_codigo"
            ),
            ClaseSenalBD.nombre.label(
                "clase_nombre"
            ),
            func.coalesce(
                conteos.c.imagenes_con_clase,
                0
            ).label(
                "imagenes_con_clase"
            ),
            func.coalesce(
                conteos.c.cantidad_anotaciones,
                0
            ).label(
                "cantidad_anotaciones"
            )
        )
        .outerjoin(
            conteos,
            conteos.c.clase_senal_id
            == ClaseSenalBD.id
        )
        .where(
            ClaseSenalBD.activa.is_(True)
        )
        .order_by(
            ClaseSenalBD.codigo
        )
    )

    return sesion.execute(
        consulta
    ).all()