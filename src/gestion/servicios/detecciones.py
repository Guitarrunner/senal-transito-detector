import os
import uuid

from pathlib import Path

from sqlalchemy.orm import Session

from src.gestion.modelos import (
    ClaseSenalBD,
    DeteccionBD,
    EvidenciaBD,
    VersionModeloBD,
)


def crear_deteccion(
    sesion: Session,
    clase_senal_id: int,
    confianza: float,
    bbox_x1: int,
    bbox_y1: int,
    bbox_x2: int,
    bbox_y2: int,
    version_modelo_id: uuid.UUID,
    evidencia_bytes: bytes,
    latitud_captura: float | None = None,
    longitud_captura: float | None = None,
    distancia_estimada: float | None = None,
):

    clase = sesion.get(
        ClaseSenalBD,
        clase_senal_id
    )

    if clase is None:
        raise ValueError(
            "Clase de señal no encontrada."
        )

    modelo = sesion.get(
        VersionModeloBD,
        version_modelo_id
    )

    if modelo is None:
        raise ValueError(
            "Versión de modelo no encontrada."
        )

    if not evidencia_bytes:
        raise ValueError(
            "La evidencia está vacía."
        )

    directorio = Path(
        os.getenv(
            "EVIDENCE_STORAGE_DIR",
            "data/evidence"
        )
    )

    directorio.mkdir(
        parents=True,
        exist_ok=True
    )

    evidencia_id = uuid.uuid4()

    nombre_archivo = (
        f"{evidencia_id}.jpg"
    )

    ruta_archivo = (
        directorio
        / nombre_archivo
    )

    ruta_archivo.write_bytes(
        evidencia_bytes
    )

    evidencia = EvidenciaBD(
        id=evidencia_id,
        ruta_archivo=str(
            ruta_archivo
        ),
        anonimizada=False
    )

    try:
        sesion.add(
            evidencia
        )

        # Garantiza que la evidencia exista
        # en PostgreSQL antes de insertar
        # la detección que la referencia.
        sesion.flush()

        deteccion = DeteccionBD(
            clase_senal_id=clase_senal_id,
            evidencia_id=evidencia.id,
            confianza=confianza,
    
            bbox_x1=bbox_x1,
            bbox_y1=bbox_y1,
            bbox_x2=bbox_x2,
            bbox_y2=bbox_y2,
    
            latitud_captura=latitud_captura,
            longitud_captura=longitud_captura,
            distancia_estimada=distancia_estimada,
    
            version_modelo_id=(
                version_modelo_id
            )
        )

        sesion.add(
            deteccion
        )

        sesion.commit()

        sesion.refresh(
            deteccion
        )

    except Exception:

        sesion.rollback()

        if ruta_archivo.exists():
            ruta_archivo.unlink()

        raise

    return deteccion, clase