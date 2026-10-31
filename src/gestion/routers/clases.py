from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.gestion.base_datos import obtener_sesion
from src.gestion.esquemas import ClaseSenalRespuesta
from src.gestion.servicios.clases import listar_clases_activas


router = APIRouter(
    prefix="/clases",
    tags=["Clases de señales"]
)


@router.get(
    "",
    response_model=list[ClaseSenalRespuesta]
)
def obtener_clases(
    sesion: Session = Depends(obtener_sesion)
):
    clases = listar_clases_activas(sesion)

    return [
        ClaseSenalRespuesta(
            id=clase.id,
            codigo=clase.codigo,
            nombre=clase.nombre,
            categoria=clase.categoria,
            activa=clase.activa
        )
        for clase in clases
    ]