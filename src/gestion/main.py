from fastapi import FastAPI
from sqlalchemy import text

from src.gestion.base_datos import SessionLocal

from src.gestion.routers.autenticacion import router as autenticacion_router
from src.gestion.routers.clases import router as clases_router
from src.gestion.routers.dataset import router as datasets_router
from src.gestion.routers.imagenes import router as imagenes_router

app = FastAPI(
    title="API de Gestión de Señales de Tránsito",
    version="0.1.0"
)

app.include_router(autenticacion_router)
app.include_router(clases_router)
app.include_router(datasets_router)
app.include_router(imagenes_router)

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