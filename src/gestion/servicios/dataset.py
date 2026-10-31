import os
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener

from src.gestion.modelos import (
    DatasetBD,
    ImagenDatasetBD,
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
        "HEIF": ".heic"
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

    nombre_fisico = (
        f"{uuid.uuid4()}{extension}"
    )

    ruta_fisica = (
        directorio_dataset / nombre_fisico
    )

    ruta_relativa = (
        Path(str(dataset.id))
        / nombre_fisico
    )

    if formato == "HEIF":
        nombre_fisico = f"{uuid.uuid4()}.jpg"
        ruta_fisica = directorio_dataset / nombre_fisico

        with Image.open(BytesIO(contenido)) as imagen:
            imagen.convert("RGB").save(
                ruta_fisica,
                format="JPEG",
                quality=95
            )

    else:
        nombre_fisico = (
            f"{uuid.uuid4()}{extensiones[formato]}"
        )

        ruta_fisica = (
            directorio_dataset / nombre_fisico
        )

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
        "HEIF": ".heic"
    }

    if formato not in extensiones:
        raise ValueError(
            "Formato no permitido. Utilice JPG, PNG, HEIC o BMP."
        )

    extension = extensiones[formato]

    directorio_base = Path(
        os.getenv(
            "DATASET_STORAGE_DIR",
            "datasets"
        )
    )

    directorio_dataset = (
        directorio_base / str(dataset.id)
    )

    directorio_dataset.mkdir(
        parents=True,
        exist_ok=True
    )

    nombre_fisico = (
        f"{uuid.uuid4()}{extension}"
    )

    ruta_fisica = (
        directorio_dataset / nombre_fisico
    )

    ruta_relativa = (
        Path(str(dataset.id))
        / nombre_fisico
    )

    ruta_fisica.write_bytes(
        contenido
    )

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