from fastapi import FastAPI
from sqlalchemy import text
from contextlib import asynccontextmanager

from src.gestion.base_datos import SessionLocal

from src.gestion.routers.autenticacion import router as autenticacion_router
from src.gestion.routers.clases import router as clases_router
from src.gestion.routers.dataset import router as datasets_router
from src.gestion.routers.imagenes import router as imagenes_router
from src.gestion.routers.modelos import router as modelos_router
from src.gestion.routers.detecciones import router as detecciones_router
from src.gestion.routers.senales import router as senales_router
from src.gestion.routers.usuarios import router as usuarios_router


from src.gestion.servicios.entrenamiento_modelo import recuperar_entrenamientos_interrumpidos

@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    recuperar_entrenamientos_interrumpidos()

    yield

app = FastAPI(
    title="API de Gestión de Señales de Tránsito",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(autenticacion_router)
app.include_router(clases_router)
app.include_router(datasets_router)
app.include_router(imagenes_router)
app.include_router(modelos_router)
app.include_router(detecciones_router)
app.include_router(senales_router)
app.include_router(usuarios_router)

@app.get("/salud")
def salud():
    return {
        "estado": "ok"
    }


@app.get("/salud/base-datos")

def salud_base_datos():
    sesion = SessionLocal()

    try:
        sesion.execute(
            text("SELECT 1")
        )

        return {
            "estado": "ok",
            "base_datos": "conectada"
        }

    finally:
        sesion.close()