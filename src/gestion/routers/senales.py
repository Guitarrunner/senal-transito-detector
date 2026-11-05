from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from src.domain.rol_usuario import (
    RolUsuario
)

from src.gestion.base_datos import (
    obtener_sesion
)

from src.gestion.esquemas import (
    SenalRespuesta
)

from src.gestion.modelos import (
    UsuarioBD
)

from src.gestion.seguridad import (
    requerir_roles
)

from src.gestion.servicios.senales import (
    listar_senales
)


router = APIRouter(
    prefix="/senales",
    tags=["Señales"]
)


@router.get(
    "",
    response_model=list[SenalRespuesta]
)
def obtener_senales(
    sesion: Session = Depends(
        obtener_sesion
    ),

    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.OPERADOR,
            RolUsuario.ADMINISTRADOR
        )
    )
):

    resultados = listar_senales(
        sesion
    )

    return [
        SenalRespuesta(
            id=senal.id,

            clase_senal_id=(
                senal.clase_senal_id
            ),

            clase_nombre=(
                clase.nombre
            ),

            latitud=senal.latitud,
            longitud=senal.longitud,

            estado_actual=(
                senal.estado_actual
            ),

            fecha_creacion=(
                senal.fecha_creacion
            ),

            fecha_actualizacion=(
                senal.fecha_actualizacion
            )
        )

        for senal, clase in resultados
    ]