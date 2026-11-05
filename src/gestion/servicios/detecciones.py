import os
import uuid

from pathlib import Path

from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session
from sqlalchemy import select

from src.domain.estado_revision import EstadoRevision

from src.gestion.servicios.senales import asociar_deteccion_a_inventario


from src.gestion.modelos import (
    ClaseSenalBD,
    DeteccionBD,
    EvidenciaBD,
    VersionModeloBD,
    RevisionDeteccionBD
)

def buscar_deteccion_existente(sesion, identificador):

    consulta = (
        select(
            DeteccionBD,
            ClaseSenalBD
        )
        .join(
            ClaseSenalBD,
            DeteccionBD.clase_senal_id
            == ClaseSenalBD.id
        )
        .where(
            DeteccionBD.id == identificador
        )
    )

    return sesion.execute(consulta).first()

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
    id_local: uuid.UUID | None = None,
    latitud_captura: float | None = None,
    longitud_captura: float | None = None,
    distancia_estimada: float | None = None,  
):

    identificador = (
        id_local if id_local is not None else uuid.uuid4()
    )

    existente = buscar_deteccion_existente(
        sesion,
        identificador
    )

    if existente is not None:
        return existente[0], existente[1]

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

    identificador = (
        id_local
        if id_local is not None
        else uuid.uuid4()
    )

    existente = buscar_deteccion_existente(
        sesion,
        identificador
    )

    if existente is not None:
        return existente[0], existente[1]

    try:
        sesion.add(
            evidencia
        )

        # Garantiza que la evidencia exista
        # en PostgreSQL antes de insertar
        # la detección que la referencia.
        sesion.flush()

        deteccion = DeteccionBD(
            id=identificador,
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

    except IntegrityError:

        sesion.rollback()
        ruta_archivo.unlink(missing_ok=True)

        # Otra solicitud pudo guardar el mismo ID
        # mientras esta se estaba procesando.
        existente = buscar_deteccion_existente(
            sesion,
            identificador
        )

        if existente is not None:
            return existente[0], existente[1]

        raise

    except Exception:

        sesion.rollback()
        ruta_archivo.unlink(missing_ok=True)
        raise

    sesion.refresh(deteccion)

    return deteccion, clase

def listar_detecciones(
    sesion: Session,
    estado: EstadoRevision | None = None,
    senal_id: uuid.UUID | None = None
):

    consulta = (
        select(
            DeteccionBD,
            ClaseSenalBD
        )
        .join(
            ClaseSenalBD,
            DeteccionBD.clase_senal_id
            == ClaseSenalBD.id
        )
    )

    if estado is not None:
        consulta = consulta.where(
            DeteccionBD.estado_revision
            == estado
        )

    if senal_id is not None:
        consulta = consulta.where(
            DeteccionBD.senal_id
            == senal_id
        )

    consulta = consulta.order_by(
        DeteccionBD.fecha_hora.desc()
    )

    resultado = sesion.execute(
        consulta
    ).all()

    return resultado

def obtener_evidencia_deteccion(
    sesion: Session,
    deteccion_id: uuid.UUID
):

    deteccion = sesion.get(
        DeteccionBD,
        deteccion_id
    )

    if deteccion is None:
        raise ValueError(
            "Detección no encontrada."
        )

    if deteccion.evidencia_id is None:
        raise ValueError(
            "La detección no tiene evidencia."
        )

    evidencia = sesion.get(
        EvidenciaBD,
        deteccion.evidencia_id
    )

    if evidencia is None:
        raise ValueError(
            "Evidencia no encontrada."
        )

    ruta = Path(
        evidencia.ruta_archivo
    )

    if not ruta.exists():
        raise ValueError(
            "El archivo de evidencia no existe."
        )

    return evidencia

def revisar_deteccion(
    sesion: Session,
    deteccion_id: uuid.UUID,
    usuario_id: uuid.UUID,
    resultado: EstadoRevision,
    comentario: str | None = None
):

    deteccion = sesion.get(
        DeteccionBD,
        deteccion_id
    )

    if deteccion is None:
        raise LookupError(
            "Detección no encontrada."
        )

    if resultado == EstadoRevision.PENDING:
        raise ValueError(
            (
                "El resultado de una revisión "
                "no puede ser PENDING."
            )
        )

    if (
        deteccion.estado_revision
        != EstadoRevision.PENDING
    ):
        raise ValueError(
            "La detección ya fue revisada."
        )

    revision = RevisionDeteccionBD(
        deteccion_id=deteccion.id,
        usuario_id=usuario_id,
        resultado=resultado,
        comentario=comentario
    )

    deteccion.estado_revision = resultado

    if resultado == EstadoRevision.APPROVED:
        asociar_deteccion_a_inventario(
            sesion=sesion,
            deteccion=deteccion
        )

    try:

        sesion.add(
            revision
        )

        sesion.commit()

        sesion.refresh(
            revision
        )

        sesion.refresh(
            deteccion
        )

    except Exception:

        sesion.rollback()
        raise

    return deteccion, revision