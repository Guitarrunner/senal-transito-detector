from sqlalchemy import select
from sqlalchemy.orm import Session

from src.gestion.modelos import ClaseSenalBD


def listar_clases_activas(
    sesion: Session
) -> list[ClaseSenalBD]:

    consulta = (
        select(ClaseSenalBD)
        .where(ClaseSenalBD.activa.is_(True))
        .order_by(ClaseSenalBD.codigo)
    )

    return list(
        sesion.scalars(consulta).all()
    )