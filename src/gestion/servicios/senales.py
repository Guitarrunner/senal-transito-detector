import math
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.gestion.modelos import (
    ClaseSenalBD,
    DeteccionBD,
    HistorialEstadoBD,
    SenalBD,
    UsuarioBD
)


def _distancia_metros(
    latitud_a: float,
    longitud_a: float,
    latitud_b: float,
    longitud_b: float
) -> float:

    radio_tierra = 6371000

    lat1 = math.radians(
        latitud_a
    )

    lat2 = math.radians(
        latitud_b
    )

    delta_lat = math.radians(
        latitud_b - latitud_a
    )

    delta_lon = math.radians(
        longitud_b - longitud_a
    )

    a = (
        math.sin(
            delta_lat / 2
        ) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(
            delta_lon / 2
        ) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radio_tierra * c


def asociar_deteccion_a_inventario(
    sesion: Session,
    deteccion: DeteccionBD,
    radio_metros: float = 20.0
):

    if (
        deteccion.latitud_captura is None
        or deteccion.longitud_captura is None
    ):
        return None

    if deteccion.senal_id is not None:
        return sesion.get(
            SenalBD,
            deteccion.senal_id
        )

    consulta = (
        select(
            SenalBD
        )
        .where(
            SenalBD.clase_senal_id == deteccion.clase_senal_id,
            SenalBD.activa.is_(True),
        )
    )

    senales = (
        sesion.execute(
            consulta
        )
        .scalars()
        .all()
    )

    for senal in senales:

        distancia = _distancia_metros(
            deteccion.latitud_captura,
            deteccion.longitud_captura,
            senal.latitud,
            senal.longitud
        )

        if distancia <= radio_metros:

            deteccion.senal_id = (
                senal.id
            )

            return senal

    senal = SenalBD(
        clase_senal_id=(
            deteccion.clase_senal_id
        ),
        latitud=(
            deteccion.latitud_captura
        ),
        longitud=(
            deteccion.longitud_captura
        )
    )

    sesion.add(
        senal
    )

    # Necesitamos el UUID antes del commit.
    sesion.flush()

    deteccion.senal_id = (
        senal.id
    )

    return senal

def retirar_senal(sesion: Session, senal_id: uuid.UUID):
    senal = sesion.get(SenalBD, senal_id, with_for_update=True)

    if senal is None:
        raise LookupError("Señal no encontrada.")

    if senal.activa:
        senal.activa = False

    sesion.commit()


def listar_senales(
    sesion: Session
):

    consulta = (
        select(
            SenalBD,
            ClaseSenalBD
        )
        .join(
            ClaseSenalBD,
            SenalBD.clase_senal_id
            == ClaseSenalBD.id
        )
        .where(SenalBD.activa.is_(True))
        .order_by(
            SenalBD.fecha_actualizacion.desc()
        )
    )

    return sesion.execute(
        consulta
    ).all()

def actualizar_estado_senal(
    sesion: Session,
    senal_id: uuid.UUID,
    usuario_id: uuid.UUID,
    estado_nuevo: str,
    comentario: str | None = None
):

    senal = sesion.get(
        SenalBD,
        senal_id
    )

    if senal is None:
        raise LookupError(
            "Señal no encontrada."
        )

    estado_anterior = (
        senal.estado_actual
    )

    if estado_anterior == estado_nuevo:
        raise ValueError(
            (
                "La señal ya posee "
                f"el estado {estado_nuevo}."
            )
        )

    historial = HistorialEstadoBD(
        senal_id=senal.id,
        usuario_id=usuario_id,

        estado_anterior=(
            estado_anterior
        ),

        estado_nuevo=(
            estado_nuevo
        ),

        comentario=comentario
    )

    senal.estado_actual = (
        estado_nuevo
    )

    try:

        sesion.add(
            historial
        )

        sesion.commit()

        sesion.refresh(
            senal
        )

        sesion.refresh(
            historial
        )

    except Exception:

        sesion.rollback()
        raise

    return senal, historial

def listar_historial_senal(
    sesion: Session,
    senal_id: uuid.UUID
):

    senal = sesion.get(
        SenalBD,
        senal_id
    )

    if senal is None:
        raise LookupError(
            "Señal no encontrada."
        )

    consulta = (
        select(
            HistorialEstadoBD,
            UsuarioBD
        )
        .join(
            UsuarioBD,
            HistorialEstadoBD.usuario_id
            == UsuarioBD.id
        )
        .where(
            HistorialEstadoBD.senal_id
            == senal_id
        )
        .order_by(
            HistorialEstadoBD
            .fecha_cambio
            .desc()
        )
    )

    return sesion.execute(
        consulta
    ).all()