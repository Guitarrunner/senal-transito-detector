import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.gestion.modelos import (
    ClaseSenalBD,
    DeteccionBD,
    SenalBD
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
            SenalBD.clase_senal_id
            == deteccion.clase_senal_id
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
        .order_by(
            SenalBD.fecha_actualizacion.desc()
        )
    )

    return sesion.execute(
        consulta
    ).all()