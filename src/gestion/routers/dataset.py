import uuid

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.orm import Session

from src.domain.rol_usuario import RolUsuario
from src.gestion.base_datos import obtener_sesion
from src.gestion.esquemas import (
    DatasetCrear,
    DatasetRespuesta,
    ImagenDatasetRespuesta,
    ErrorCargaImagen,
    CargaImagenesBulkRespuesta
)
from src.gestion.modelos import UsuarioBD
from src.gestion.seguridad import requerir_roles
from src.gestion.servicios.dataset import (
    crear_dataset as crear_dataset_servicio,
    guardar_imagen_dataset,
    listar_datasets as listar_datasets_servicio,
    listar_imagenes_dataset,
    obtener_dataset,
)

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"]
)


@router.post(
    "",
    response_model=DatasetRespuesta,
    status_code=status.HTTP_201_CREATED
)
def crear_dataset(
    datos: DatasetCrear,
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    dataset = crear_dataset_servicio(
        sesion=sesion,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        creado_por=usuario.id
    )

    return DatasetRespuesta(
        id=dataset.id,
        nombre=dataset.nombre,
        descripcion=dataset.descripcion,
        creado_por=dataset.creado_por,
        fecha_creacion=dataset.fecha_creacion
    )


@router.get(
    "",
    response_model=list[DatasetRespuesta]
)
def obtener_datasets(
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    datasets = listar_datasets_servicio(
        sesion
    )

    return [
        DatasetRespuesta(
            id=dataset.id,
            nombre=dataset.nombre,
            descripcion=dataset.descripcion,
            creado_por=dataset.creado_por,
            fecha_creacion=dataset.fecha_creacion
        )
        for dataset in datasets
    ]

@router.post(
    "/{dataset_id}/imagenes",
    response_model=ImagenDatasetRespuesta,
    status_code=status.HTTP_201_CREATED
)
async def subir_imagen_dataset(
    dataset_id: uuid.UUID,
    archivo: UploadFile = File(...),
    grupo_fisico: str | None = Form(None),
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    dataset = obtener_dataset(
        sesion,
        dataset_id
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset no encontrado."
        )

    contenido = await archivo.read()

    try:
        imagen = guardar_imagen_dataset(
            sesion=sesion,
            dataset=dataset,
            nombre_original=(
                archivo.filename
                or "imagen"
            ),
            contenido=contenido,
            grupo_fisico=grupo_fisico
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    return ImagenDatasetRespuesta(
        id=imagen.id,
        dataset_id=imagen.dataset_id,
        nombre_archivo=imagen.nombre_archivo,
        ancho=imagen.ancho,
        alto=imagen.alto,
        conjunto=imagen.conjunto,
        grupo_fisico=imagen.grupo_fisico,
        evidencia_id=imagen.evidencia_id,
        fecha_agregada=imagen.fecha_agregada
    )

@router.get(
    "/{dataset_id}/imagenes",
    response_model=list[ImagenDatasetRespuesta]
)
def obtener_imagenes_dataset(
    dataset_id: uuid.UUID,
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    dataset = obtener_dataset(
        sesion,
        dataset_id
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset no encontrado."
        )

    imagenes = listar_imagenes_dataset(
        sesion,
        dataset_id
    )

    return [
        ImagenDatasetRespuesta(
            id=imagen.id,
            dataset_id=imagen.dataset_id,
            nombre_archivo=imagen.nombre_archivo,
            ancho=imagen.ancho,
            alto=imagen.alto,
            conjunto=imagen.conjunto,
            grupo_fisico=imagen.grupo_fisico,
            evidencia_id=imagen.evidencia_id,
            fecha_agregada=imagen.fecha_agregada
        )
        for imagen in imagenes
    ]

@router.post(
    "/{dataset_id}/imagenes/bulk",
    response_model=CargaImagenesBulkRespuesta,
    status_code=status.HTTP_201_CREATED
)
async def subir_imagenes_bulk(
    dataset_id: uuid.UUID,
    archivos: list[UploadFile] = File(...),
    sesion: Session = Depends(obtener_sesion),
    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR
        )
    )
):
    dataset = obtener_dataset(
        sesion,
        dataset_id
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset no encontrado."
        )

    cargadas = []
    errores = []

    for archivo in archivos:

        contenido = await archivo.read()

        try:
            imagen = guardar_imagen_dataset(
                sesion=sesion,
                dataset=dataset,
                nombre_original=(
                    archivo.filename
                    or "imagen"
                ),
                contenido=contenido,
                grupo_fisico=None
            )

            cargadas.append(
                ImagenDatasetRespuesta(
                    id=imagen.id,
                    dataset_id=imagen.dataset_id,
                    nombre_archivo=imagen.nombre_archivo,
                    ancho=imagen.ancho,
                    alto=imagen.alto,
                    conjunto=imagen.conjunto,
                    grupo_fisico=imagen.grupo_fisico,
                    evidencia_id=imagen.evidencia_id,
                    fecha_agregada=imagen.fecha_agregada
                )
            )

        except ValueError as error:
            errores.append(
                ErrorCargaImagen(
                    nombre_archivo=(
                        archivo.filename
                        or "imagen"
                    ),
                    error=str(error)
                )
            )

    return CargaImagenesBulkRespuesta(
        cargadas=cargadas,
        errores=errores
    )