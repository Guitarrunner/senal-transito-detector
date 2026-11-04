import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy.orm import Session

from src.domain.rol_usuario import (
    RolUsuario
)

from src.gestion.base_datos import (
    obtener_sesion
)

from src.gestion.esquemas import (
    DeteccionRespuesta
)

from src.gestion.modelos import (
    UsuarioBD
)

from src.gestion.seguridad import (
    requerir_roles
)

from src.gestion.servicios.detecciones import (
    crear_deteccion
)


router = APIRouter(
    prefix="/detecciones",
    tags=["Detecciones"]
)


@router.post(
    "",
    response_model=DeteccionRespuesta,
    status_code=status.HTTP_201_CREATED
)
async def registrar_deteccion(
    clase_senal_id: int = Form(...),
    confianza: float = Form(...),

    bbox_x1: int = Form(...),
    bbox_y1: int = Form(...),
    bbox_x2: int = Form(...),
    bbox_y2: int = Form(...),

    version_modelo_id: uuid.UUID = Form(...),

    latitud_captura: float | None = Form(None),
    longitud_captura: float | None = Form(None),
    distancia_estimada: float | None = Form(None),

    evidencia: UploadFile = File(...),

    sesion: Session = Depends(
        obtener_sesion
    ),

    usuario: UsuarioBD = Depends(
        requerir_roles(
            RolUsuario.CAMPO,
            RolUsuario.ADMINISTRADOR
        )
    )
):

    contenido = await evidencia.read()

    try:
        deteccion, clase = crear_deteccion(
            sesion=sesion,

            clase_senal_id=(
                clase_senal_id
            ),

            confianza=confianza,

            bbox_x1=bbox_x1,
            bbox_y1=bbox_y1,
            bbox_x2=bbox_x2,
            bbox_y2=bbox_y2,

            version_modelo_id=(
                version_modelo_id
            ),

            evidencia_bytes=contenido,

            latitud_captura=(
                latitud_captura
            ),

            longitud_captura=(
                longitud_captura
            ),

            distancia_estimada=(
                distancia_estimada
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error)
        )

    return DeteccionRespuesta(
        id=deteccion.id,

        clase_senal_id=(
            deteccion.clase_senal_id
        ),

        clase_nombre=(
            clase.nombre
        ),

        evidencia_id=(
            deteccion.evidencia_id
        ),

        confianza=(
            deteccion.confianza
        ),

        fecha_hora=(
            deteccion.fecha_hora
        ),

        bbox_x1=deteccion.bbox_x1,
        bbox_y1=deteccion.bbox_y1,
        bbox_x2=deteccion.bbox_x2,
        bbox_y2=deteccion.bbox_y2,

        latitud_captura=(
            deteccion.latitud_captura
        ),

        longitud_captura=(
            deteccion.longitud_captura
        ),

        distancia_estimada=(
            deteccion.distancia_estimada
        ),

        estado_revision=(
            deteccion.estado_revision
        ),

        version_modelo_id=(
            deteccion.version_modelo_id
        )
    )