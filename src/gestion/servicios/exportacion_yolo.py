import os
import random
import shutil
import uuid
from collections import defaultdict
from pathlib import Path

import yaml
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.conjunto_dataset import (
    ConjuntoDataset
)
from src.gestion.modelos import (
    DatasetBD,
    ImagenDatasetBD,
    AnotacionBD,
    ClaseSenalBD,
)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

CLASES_EXCLUIDAS = {
    "TREN"
}


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def _inferir_grupo_fisico(
    nombre_archivo: str
) -> str:
    """
    Ejemplo:

    ALTO_03_05.HEIC
        ->
    ALTO_03

    NOESTACIONAR_02_04.HEIC
        ->
    NOESTACIONAR_02
    """

    nombre = Path(
        nombre_archivo
    ).stem

    partes = nombre.rsplit(
        "_",
        1
    )

    if len(partes) != 2:
        raise ValueError(
            (
                "No se pudo determinar el grupo "
                "físico de "
                f"{nombre_archivo}."
            )
        )

    return partes[0].upper()


def _inferir_clase_grupo(
    grupo_fisico: str
) -> str:
    """
    Ejemplo:

    ALTO_03
        ->
    ALTO

    NOESTACIONAR_02
        ->
    NOESTACIONAR
    """

    partes = grupo_fisico.rsplit(
        "_",
        1
    )

    if len(partes) != 2:
        raise ValueError(
            (
                "No se pudo determinar la clase "
                f"del grupo {grupo_fisico}."
            )
        )

    return partes[0].upper()


# ==========================================================
# EXPORTACIÓN
# ==========================================================

def exportar_dataset_yolo(
    sesion: Session,
    dataset_id: uuid.UUID,
    semilla: int = 42
):

    # ------------------------------------------------------
    # 1. Validar dataset
    # ------------------------------------------------------

    dataset = sesion.get(
        DatasetBD,
        dataset_id
    )

    if dataset is None:
        raise ValueError(
            "Dataset no encontrado."
        )

    # ------------------------------------------------------
    # 2. Obtener imágenes
    # ------------------------------------------------------

    imagenes = list(
        sesion.scalars(
            select(
                ImagenDatasetBD
            )
            .where(
                ImagenDatasetBD.dataset_id
                == dataset_id
            )
        ).all()
    )

    if not imagenes:
        raise ValueError(
            "El dataset no contiene imágenes."
        )

    ids_imagenes = [
        imagen.id
        for imagen in imagenes
    ]

    # ------------------------------------------------------
    # 3. Obtener anotaciones
    # ------------------------------------------------------

    anotaciones = list(
        sesion.scalars(
            select(
                AnotacionBD
            )
            .where(
                AnotacionBD.imagen_id.in_(
                    ids_imagenes
                )
            )
        ).all()
    )

    if not anotaciones:
        raise ValueError(
            "El dataset no contiene anotaciones."
        )

    # ------------------------------------------------------
    # 4. Obtener solo clases utilizadas
    # ------------------------------------------------------

    ids_clases_usadas = {
        anotacion.clase_senal_id
        for anotacion in anotaciones
    }

    clases = list(
        sesion.scalars(
            select(
                ClaseSenalBD
            )
            .where(
                ClaseSenalBD.id.in_(
                    ids_clases_usadas
                )
            )
            .order_by(
                ClaseSenalBD.codigo
            )
        ).all()
    )

    # Eliminar temporalmente clases que no queremos
    # entrenar en esta primera versión.

    clases = [
        clase
        for clase in clases
        if (
            clase.nombre.upper()
            not in CLASES_EXCLUIDAS
        )
    ]

    if not clases:
        raise ValueError(
            (
                "No existen clases disponibles "
                "para exportar."
            )
        )

    # ------------------------------------------------------
    # 5. Crear IDs consecutivos para YOLO
    # ------------------------------------------------------

    id_yolo_por_clase = {
        clase.id: indice
        for indice, clase in enumerate(
            clases
        )
    }

    # Ejemplo:
    #
    # PostgreSQL:
    # ALTO -> id 1
    # CEDA -> id 2
    # NOIZQ -> id 5
    #
    # YOLO:
    # ALTO -> 0
    # CEDA -> 1
    # NOIZQ -> 2

    # ------------------------------------------------------
    # 6. Agrupar anotaciones por imagen
    # ------------------------------------------------------

    anotaciones_por_imagen = (
        defaultdict(list)
    )

    for anotacion in anotaciones:

        # Si la anotación pertenece a una clase
        # excluida, no la consideramos.

        if (
            anotacion.clase_senal_id
            not in id_yolo_por_clase
        ):
            continue

        anotaciones_por_imagen[
            anotacion.imagen_id
        ].append(
            anotacion
        )

    # ------------------------------------------------------
    # 7. Agrupar imágenes por señal física
    # ------------------------------------------------------

    grupos_por_clase = defaultdict(
        lambda: defaultdict(list)
    )

    imagenes_omitidas = 0

    for imagen in imagenes:

        # Si después de excluir ciertas clases
        # la imagen no tiene anotaciones útiles,
        # no se exporta.

        if not anotaciones_por_imagen[
            imagen.id
        ]:
            imagenes_omitidas += 1
            continue

        grupo_fisico = (
            imagen.grupo_fisico
            or _inferir_grupo_fisico(
                imagen.nombre_archivo
            )
        ).upper()

        clase_grupo = (
            _inferir_clase_grupo(
                grupo_fisico
            )
        ).upper()

        # TREN queda completamente fuera
        # de esta primera versión.

        if (
            clase_grupo
            in CLASES_EXCLUIDAS
        ):
            imagenes_omitidas += 1
            continue

        grupos_por_clase[
            clase_grupo
        ][
            grupo_fisico
        ].append(
            imagen
        )

        # Normalizamos también el valor almacenado
        # en la base de datos.

        imagen.grupo_fisico = (
            grupo_fisico
        )

    # ------------------------------------------------------
    # 8. Crear división TRAIN / VAL / TEST
    # ------------------------------------------------------

    randomizador = random.Random(
        semilla
    )

    asignacion_grupos = {}

    for (
        clase_grupo,
        grupos
    ) in grupos_por_clase.items():

        nombres_grupos = list(
            grupos.keys()
        )

        if len(nombres_grupos) < 3:
            raise ValueError(
                (
                    f"La clase {clase_grupo} "
                    f"tiene solo "
                    f"{len(nombres_grupos)} "
                    "señales físicas. "
                    "Se requieren al menos 3 "
                    "para separar train, "
                    "val y test."
                )
            )

        randomizador.shuffle(
            nombres_grupos
        )

        cantidad = len(
            nombres_grupos
        )

        # Aproximadamente:
        #
        # 70 % train
        # 15 % val
        # 15 % test

        cantidad_val = max(
            1,
            round(
                cantidad * 0.15
            )
        )

        cantidad_test = max(
            1,
            round(
                cantidad * 0.15
            )
        )

        # Nos aseguramos de dejar
        # al menos un grupo para train.

        while (
            cantidad_val
            + cantidad_test
            >= cantidad
        ):

            if cantidad_val > 1:
                cantidad_val -= 1

            elif cantidad_test > 1:
                cantidad_test -= 1

            else:
                break

        cantidad_train = (
            cantidad
            - cantidad_val
            - cantidad_test
        )

        grupos_train = (
            nombres_grupos[
                :cantidad_train
            ]
        )

        grupos_val = (
            nombres_grupos[
                cantidad_train:
                cantidad_train
                + cantidad_val
            ]
        )

        grupos_test = (
            nombres_grupos[
                cantidad_train
                + cantidad_val:
            ]
        )

        for grupo in grupos_train:

            asignacion_grupos[
                grupo
            ] = ConjuntoDataset.TRAIN

        for grupo in grupos_val:

            asignacion_grupos[
                grupo
            ] = ConjuntoDataset.VAL

        for grupo in grupos_test:

            asignacion_grupos[
                grupo
            ] = ConjuntoDataset.TEST

    # ------------------------------------------------------
    # 9. Preparar directorios
    # ------------------------------------------------------

    directorio_origen = Path(
        os.getenv(
            "DATASET_STORAGE_DIR",
            "datasets"
        )
    )

    directorio_exportacion = (
        Path(
            os.getenv(
                "YOLO_EXPORT_DIR",
                "datasets/exportados"
            )
        )
        / str(dataset_id)
    )

    # Si ya habíamos exportado antes,
    # eliminamos esa exportación.

    if directorio_exportacion.exists():

        shutil.rmtree(
            directorio_exportacion
        )

    for conjunto in (
        "train",
        "val",
        "test"
    ):

        (
            directorio_exportacion
            / "images"
            / conjunto
        ).mkdir(
            parents=True,
            exist_ok=True
        )

        (
            directorio_exportacion
            / "labels"
            / conjunto
        ).mkdir(
            parents=True,
            exist_ok=True
        )

    conteos = {
        "train": 0,
        "val": 0,
        "test": 0
    }

    # ------------------------------------------------------
    # 10. Exportar imágenes y anotaciones
    # ------------------------------------------------------

    for imagen in imagenes:

        anotaciones_imagen = (
            anotaciones_por_imagen[
                imagen.id
            ]
        )

        if not anotaciones_imagen:
            continue

        grupo_fisico = (
            imagen.grupo_fisico
            or _inferir_grupo_fisico(
                imagen.nombre_archivo
            )
        ).upper()

        clase_grupo = (
            _inferir_clase_grupo(
                grupo_fisico
            )
        ).upper()

        if (
            clase_grupo
            in CLASES_EXCLUIDAS
        ):
            continue

        # El grupo tiene que haber sido asignado
        # anteriormente a train, val o test.

        if (
            grupo_fisico
            not in asignacion_grupos
        ):
            continue

        conjunto = (
            asignacion_grupos[
                grupo_fisico
            ]
        )

        imagen.conjunto = conjunto

        nombre_conjunto = (
            conjunto.value.lower()
        )

        # --------------------------------------------------
        # Imagen
        # --------------------------------------------------

        ruta_origen = (
            directorio_origen
            / imagen.ruta_archivo
        )

        if not ruta_origen.exists():
            raise ValueError(
                (
                    "No se encontró el archivo "
                    f"{ruta_origen}."
                )
            )

        # Utilizamos UUID para evitar conflictos
        # de nombres.

        nombre_exportado = str(
            imagen.id
        )

        ruta_imagen_destino = (
            directorio_exportacion
            / "images"
            / nombre_conjunto
            / f"{nombre_exportado}.jpg"
        )

        ruta_label_destino = (
            directorio_exportacion
            / "labels"
            / nombre_conjunto
            / f"{nombre_exportado}.txt"
        )

        # Convertimos todo a JPEG para tener
        # una estructura uniforme.

        with Image.open(
            ruta_origen
        ) as imagen_pil:

            imagen_pil.convert(
                "RGB"
            ).save(
                ruta_imagen_destino,
                format="JPEG",
                quality=95
            )

        # --------------------------------------------------
        # Labels YOLO
        # --------------------------------------------------

        lineas = []

        for anotacion in (
            anotaciones_imagen
        ):

            if (
                anotacion.clase_senal_id
                not in id_yolo_por_clase
            ):
                continue

            ancho = imagen.ancho
            alto = imagen.alto

            # Bounding box original:
            #
            # x1, y1 --------
            # |              |
            # |              |
            # -------- x2, y2
            #
            # YOLO necesita:
            #
            # centro_x
            # centro_y
            # ancho
            # alto
            #
            # normalizados entre 0 y 1.

            centro_x = (
                (
                    anotacion.bbox_x1
                    + anotacion.bbox_x2
                )
                / 2
                / ancho
            )

            centro_y = (
                (
                    anotacion.bbox_y1
                    + anotacion.bbox_y2
                )
                / 2
                / alto
            )

            ancho_bbox = (
                (
                    anotacion.bbox_x2
                    - anotacion.bbox_x1
                )
                / ancho
            )

            alto_bbox = (
                (
                    anotacion.bbox_y2
                    - anotacion.bbox_y1
                )
                / alto
            )

            id_yolo = (
                id_yolo_por_clase[
                    anotacion.clase_senal_id
                ]
            )

            lineas.append(
                (
                    f"{id_yolo} "
                    f"{centro_x:.6f} "
                    f"{centro_y:.6f} "
                    f"{ancho_bbox:.6f} "
                    f"{alto_bbox:.6f}"
                )
            )

        # Una imagen puede tener múltiples
        # anotaciones.

        ruta_label_destino.write_text(
            "\n".join(
                lineas
            ),
            encoding="utf-8"
        )

        conteos[
            nombre_conjunto
        ] += 1

    # ------------------------------------------------------
    # 11. Crear dataset.yaml
    # ------------------------------------------------------

    configuracion_yolo = {
        "path": str(
            directorio_exportacion.resolve()
        ),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {
            indice: clase.nombre
            for indice, clase in enumerate(
                clases
            )
        }
    }

    ruta_yaml = (
        directorio_exportacion
        / "dataset.yaml"
    )

    with open(
        ruta_yaml,
        "w",
        encoding="utf-8"
    ) as archivo_yaml:

        yaml.safe_dump(
            configuracion_yolo,
            archivo_yaml,
            allow_unicode=True,
            sort_keys=False
        )

    # ------------------------------------------------------
    # 12. Guardar conjunto y grupo físico en BD
    # ------------------------------------------------------

    try:

        sesion.commit()

    except Exception:

        sesion.rollback()
        raise

    # ------------------------------------------------------
    # 13. Resultado
    # ------------------------------------------------------

    return {
        "ruta_dataset": str(
            directorio_exportacion
        ),
        "ruta_yaml": str(
            ruta_yaml
        ),
        "imagenes_train": (
            conteos["train"]
        ),
        "imagenes_val": (
            conteos["val"]
        ),
        "imagenes_test": (
            conteos["test"]
        ),
        "imagenes_omitidas": (
            imagenes_omitidas
        )
    }