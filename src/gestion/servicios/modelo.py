import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.gestion.modelos import (
    VersionModeloBD
)


def listar_modelos(
    sesion: Session
) -> list[VersionModeloBD]:

    return list(
        sesion.scalars(
            select(
                VersionModeloBD
            )
            .order_by(
                VersionModeloBD
                .fecha_entrenamiento
                .desc()
            )
        ).all()
    )


def obtener_modelo(
    sesion: Session,
    modelo_id: uuid.UUID
) -> VersionModeloBD | None:

    return sesion.get(
        VersionModeloBD,
        modelo_id
    )


def activar_modelo(
    sesion: Session,
    modelo_id: uuid.UUID
) -> VersionModeloBD:

    modelo = obtener_modelo(
        sesion,
        modelo_id
    )

    if modelo is None:
        raise ValueError(
            "Modelo no encontrado."
        )

    # Solo debe existir un modelo activo.
    sesion.execute(
        update(
            VersionModeloBD
        )
        .values(
            activo=False
        )
    )

    modelo.activo = True

    sesion.commit()
    sesion.refresh(
        modelo
    )

    return modelo