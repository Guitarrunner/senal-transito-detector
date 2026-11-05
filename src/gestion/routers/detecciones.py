import uuid
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from src.domain.rol_usuario import (
    RolUsuario
)

from src.gestion.base_datos import (
    obtener_sesion
)

from src.gestion.esquemas import (
    DeteccionRespuesta, RevisionDeteccionCrear,
    RevisionDeteccionRespuesta
)

from src.gestion.modelos import (
    UsuarioBD
)

from src.gestion.seguridad import (
    requerir_roles
)

from src.gestion.servicios.detecciones import (
    crear_deteccion, listar_detecciones, obtener_evidencia_deteccion, revisar_deteccion
)

from src.domain.estado_revision import EstadoRevision



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
    id_local: uuid.UUID | None = Form(None),

    evidencia: UploadFile = File(...),

    anonimizada: bool = Form(False),

    sesion: Session = Depends(
        obtener_sesion
    ),

    precision_ubicacion_m: float | None = Form(
        None,
        ge=0
    ),
    fecha_ubicacion: datetime | None = Form(None),
    fuente_ubicacion: str | None = Form(
        None,
        max_length=50
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
            ),

            id_local= id_local,

            anonimizada=anonimizada,
            fecha_ubicacion=fecha_ubicacion,
            fuente_ubicacion=fuente_ubicacion,
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
        ),

        precision_ubicacion_m=deteccion.precision_ubicacion_m,
        fecha_ubicacion=deteccion.fecha_ubicacion,
        fuente_ubicacion=deteccion.fuente_ubicacion,
    )

@router.get(
    "",
    response_model=list[DeteccionRespuesta]
)
def obtener_detecciones(
    estado: EstadoRevision | None = None,
    senal_id: uuid.UUID | None = None,

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

    resultados = listar_detecciones(
        sesion=sesion,
        estado=estado,
        senal_id=senal_id
    )

    respuestas = []

    for deteccion, clase in resultados:

        respuestas.append(
            DeteccionRespuesta(
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

                bbox_x1=(
                    deteccion.bbox_x1
                ),

                bbox_y1=(
                    deteccion.bbox_y1
                ),

                bbox_x2=(
                    deteccion.bbox_x2
                ),

                bbox_y2=(
                    deteccion.bbox_y2
                ),

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
                ),

                precision_ubicacion_m=deteccion.precision_ubicacion_m,
                fecha_ubicacion=deteccion.fecha_ubicacion,
                fuente_ubicacion=deteccion.fuente_ubicacion,
            )
        )

    return respuestas

@router.get(
    "/{deteccion_id}/evidencia"
)
def obtener_evidencia(
    deteccion_id: uuid.UUID,

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

    try:
        evidencia = (
            obtener_evidencia_deteccion(
                sesion=sesion,
                deteccion_id=deteccion_id
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    return FileResponse(
        path=evidencia.ruta_archivo,
        media_type="image/jpeg"
    )

@router.post(
    "/{deteccion_id}/revision",
    response_model=RevisionDeteccionRespuesta,
    status_code=status.HTTP_201_CREATED
)
def registrar_revision_deteccion(
    deteccion_id: uuid.UUID,
    datos: RevisionDeteccionCrear,

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

    try:

        deteccion, revision = (
            revisar_deteccion(
                sesion=sesion,
                deteccion_id=deteccion_id,
                usuario_id=usuario.id,
                resultado=datos.resultado,
                comentario=datos.comentario
            )
        )

    except LookupError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error)
        )

    return RevisionDeteccionRespuesta(
        id=revision.id,

        deteccion_id=(
            revision.deteccion_id
        ),

        usuario_id=(
            revision.usuario_id
        ),

        resultado=(
            revision.resultado
        ),

        comentario=(
            revision.comentario
        ),

        fecha_revision=(
            revision.fecha_revision
        )
    )