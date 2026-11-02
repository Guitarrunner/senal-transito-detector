import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import requests
import torch
import multiprocessing
from sqlalchemy import select
from sqlalchemy.orm import Session
from ultralytics import YOLO

from src.domain.estado_entrenamiento import (
    EstadoEntrenamiento
)
from src.gestion.base_datos import (
    SessionLocal
)
from src.gestion.modelos import (
    DatasetBD,
    EntrenamientoModeloBD,
    VersionModeloBD,
)
from src.gestion.servicios.exportacion_yolo import (
    exportar_dataset_yolo
)


def obtener_dispositivo() -> str:

    if torch.cuda.is_available():
        return "0"

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return "mps"

    return "cpu"


def crear_entrenamiento(
    sesion: Session,
    dataset_id: uuid.UUID,
    creado_por: uuid.UUID,
    version: str,
    modelo_base: str,
    epocas: int,
    imgsz: int,
    batch: int
) -> EntrenamientoModeloBD:

    dataset = sesion.get(
        DatasetBD,
        dataset_id
    )

    if dataset is None:
        raise ValueError(
            "Dataset no encontrado."
        )

    # Evitar dos entrenamientos simultáneos.
    entrenamiento_en_curso = (
        sesion.scalar(
            select(
                EntrenamientoModeloBD
            )
            .where(
                EntrenamientoModeloBD.estado.in_(
                    [
                        EstadoEntrenamiento.PENDIENTE,
                        EstadoEntrenamiento.ENTRENANDO,
                    ]
                )
            )
        )
    )

    if entrenamiento_en_curso is not None:
        raise ValueError(
            (
                "Ya existe un entrenamiento "
                "en ejecución."
            )
        )

    # No permitir una versión que ya produjo
    # un modelo.
    version_existente = sesion.scalar(
        select(
            VersionModeloBD
        )
        .where(
            VersionModeloBD.version
            == version
        )
    )

    if version_existente is not None:
        raise ValueError(
            (
                f"Ya existe la versión "
                f"{version}."
            )
        )

    entrenamiento = EntrenamientoModeloBD(
        dataset_id=dataset_id,
        creado_por=creado_por,
        version=version,
        modelo_base=modelo_base,
        epocas=epocas,
        imgsz=imgsz,
        batch=batch,
        estado=(
            EstadoEntrenamiento.PENDIENTE
        ),
        epoca_actual=0
    )

    sesion.add(
        entrenamiento
    )

    sesion.commit()
    sesion.refresh(
        entrenamiento
    )

    return entrenamiento


def obtener_entrenamiento(
    self,
    entrenamiento_id: str
):

    try:
        respuesta = self.sesion.get(
            (
                f"{self.api_url}"
                "/modelos/entrenamientos/"
                f"{entrenamiento_id}"
            ),
            headers=self._headers(),
            timeout=10
        )

    except requests.RequestException as error:
        raise RuntimeError(
            (
                "No se pudo consultar "
                "el entrenamiento."
            )
        ) from error

    self._procesar_respuesta(
        respuesta
    )

    return respuesta.json()


def listar_entrenamientos(self):

    try:
        respuesta = self.sesion.get(
            (
                f"{self.api_url}"
                "/modelos/entrenamientos"
            ),
            headers=self._headers(),
            timeout=10
        )

    except requests.RequestException as error:
        raise RuntimeError(
            (
                "No se pudo consultar el estado "
                "de los entrenamientos."
            )
        ) from error

    self._procesar_respuesta(
        respuesta
    )

    return respuesta.json()


def ejecutar_entrenamiento(
    entrenamiento_id: uuid.UUID
):
    """
    Esta función se ejecuta fuera del request HTTP.

    Es importante que cree su propia sesión SQLAlchemy
    y NO reutilice la sesión del endpoint.
    """

    sesion = SessionLocal()

    try:
        entrenamiento = sesion.get(
            EntrenamientoModeloBD,
            entrenamiento_id
        )

        if entrenamiento is None:
            return

        entrenamiento.fecha_inicio = (
            datetime.now()
        )

        entrenamiento.mensaje_error = None

        sesion.commit()

        resultado_exportacion = (
            exportar_dataset_yolo(
                sesion,
                entrenamiento.dataset_id
            )
        )

        ruta_yaml = Path(
            resultado_exportacion[
                "ruta_yaml"
            ]
        ).resolve()

        if not ruta_yaml.exists():
            raise RuntimeError(
                (
                    "No se encontró dataset.yaml "
                    "después de la exportación."
                )
            )

        entrenamiento = sesion.get(
            EntrenamientoModeloBD,
            entrenamiento_id
        )

        entrenamiento.estado = (
            EstadoEntrenamiento.ENTRENANDO
        )

        sesion.commit()

        dispositivo = (
            obtener_dispositivo()
        )

        print(
            (
                f"Entrenamiento "
                f"{entrenamiento.version} "
                f"usando {dispositivo}"
            )
        )

        modelo = YOLO(
            entrenamiento.modelo_base
        )

        def actualizar_epoca(
            trainer
        ):
            """
            Ultralytics llama este callback al terminar
            cada época completa de entrenamiento +
            validación.
            """

            nueva_sesion = SessionLocal()

            try:
                entrenamiento_actual = (
                    nueva_sesion.get(
                        EntrenamientoModeloBD,
                        entrenamiento_id
                    )
                )

                if entrenamiento_actual is None:
                    return

                entrenamiento_actual.epoca_actual = min(
                    trainer.epoch + 1,
                    entrenamiento_actual.epocas
                )

                nueva_sesion.commit()

            finally:
                nueva_sesion.close()

        modelo.add_callback(
            "on_fit_epoch_end",
            actualizar_epoca
        )

        version_segura = re.sub(
            r"[^A-Za-z0-9_.-]",
            "_",
            entrenamiento.version
        )

        nombre_ejecucion = (
            f"{version_segura}_"
            f"{str(entrenamiento.id)[:8]}"
        )

        modelo.train(
            data=str(
                ruta_yaml
            ),
            epochs=entrenamiento.epocas,
            imgsz=entrenamiento.imgsz,
            batch=entrenamiento.batch,
            device=dispositivo,
            project=(
                "modelos/entrenamientos"
            ),
            name=nombre_ejecucion,
            patience=15,
            save=True,
            plots=True,

            # Más estable para nuestra
            # ejecución en segundo plano.
            workers=0
        )

        ruta_best = Path(
            modelo.trainer.best
        )

        if not ruta_best.exists():
            raise RuntimeError(
                (
                    "El entrenamiento terminó "
                    "pero no se encontró best.pt."
                )
            )

        directorio_modelo = (
            Path(
                "modelos/versiones"
            )
            / version_segura
        )

        directorio_modelo.mkdir(
            parents=True,
            exist_ok=True
        )

        ruta_modelo_final = (
            directorio_modelo
            / "best.pt"
        )

        shutil.copy2(
            ruta_best,
            ruta_modelo_final
        )

        modelo_final = YOLO(
            str(
                ruta_modelo_final
            )
        )

        metricas = modelo_final.val(
            data=str(
                ruta_yaml
            ),
            split="test",
            device=dispositivo,
            workers=0
        )

        precision = float(
            metricas.box.mp
        )

        recall = float(
            metricas.box.mr
        )

        map_50 = float(
            metricas.box.map50
        )

        map_50_95 = float(
            metricas.box.map
        )

        latencia = None
        fps = None

        if (
            metricas.speed
            and "inference"
            in metricas.speed
        ):
            latencia = float(
                metricas.speed[
                    "inference"
                ]
            )

            if latencia > 0:
                fps = (
                    1000.0
                    / latencia
                )

        version_modelo = VersionModeloBD(
            dataset_id=(
                entrenamiento.dataset_id
            ),
            version=(
                entrenamiento.version
            ),
            ruta_modelo=str(
                ruta_modelo_final
            ),
            precision=precision,
            recall=recall,
            map_50=map_50,
            map_50_95=map_50_95,
            latencia_promedio_ms=(
                latencia
            ),
            fps=fps,
            activo=False,
            fecha_entrenamiento=(
                datetime.now()
            )
        )

        sesion.add(
            version_modelo
        )

        sesion.flush()

        entrenamiento = sesion.get(
            EntrenamientoModeloBD,
            entrenamiento_id
        )

        entrenamiento.estado = (
            EstadoEntrenamiento.COMPLETADO
        )

        entrenamiento.version_modelo_id = (
            version_modelo.id
        )

        entrenamiento.fecha_fin = (
            datetime.now()
        )

        sesion.commit()

    except Exception as error:

        sesion.rollback()

        entrenamiento = sesion.get(
            EntrenamientoModeloBD,
            entrenamiento_id
        )

        if entrenamiento is not None:

            entrenamiento.estado = (
                EstadoEntrenamiento.ERROR
            )

            entrenamiento.mensaje_error = (
                str(error)[:1000]
            )

            entrenamiento.fecha_fin = (
                datetime.now()
            )

            sesion.commit()

        print(
            (
                "Error durante entrenamiento "
                f"{entrenamiento_id}: "
                f"{error}"
            )
        )

    finally:
        sesion.close()

def iniciar_proceso_entrenamiento(
    entrenamiento_id: uuid.UUID
):
    """
    Ejecuta YOLO en un proceso independiente.

    Así el entrenamiento no bloquea
    el proceso de FastAPI.
    """

    contexto = multiprocessing.get_context(
        "spawn"
    )

    proceso = contexto.Process(
        target=ejecutar_entrenamiento,
        args=(
            entrenamiento_id,
        )
    )

    proceso.start()