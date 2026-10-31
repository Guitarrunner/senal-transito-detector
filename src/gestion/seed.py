import os

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import select

from src.domain.rol_usuario import RolUsuario
from src.gestion.base_datos import SessionLocal
from src.gestion.modelos import ClaseSenalBD, UsuarioBD


load_dotenv()


def generar_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")

    password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return password_hash.decode("utf-8")


def crear_usuarios_iniciales(sesion):
    usuarios = [
        {
            "nombre_usuario": "admin",
            "password": os.getenv("SEED_ADMIN_PASSWORD"),
            "rol": RolUsuario.ADMINISTRADOR
        },
        {
            "nombre_usuario": "operador",
            "password": os.getenv("SEED_OPERADOR_PASSWORD"),
            "rol": RolUsuario.OPERADOR
        },
        {
            "nombre_usuario": "campo",
            "password": os.getenv("SEED_CAMPO_PASSWORD"),
            "rol": RolUsuario.CAMPO
        }
    ]

    for datos in usuarios:

        usuario_existente = sesion.scalar(
            select(UsuarioBD).where(
                UsuarioBD.nombre_usuario
                == datos["nombre_usuario"]
            )
        )

        if usuario_existente is not None:
            continue

        if datos["password"] is None:
            raise RuntimeError(
                f"No se encontró contraseña para "
                f"{datos['nombre_usuario']}."
            )

        usuario = UsuarioBD(
            nombre_usuario=datos["nombre_usuario"],
            password_hash=generar_hash(
                datos["password"]
            ),
            rol=datos["rol"],
            activo=True
        )

        sesion.add(usuario)


def crear_clases_iniciales(sesion):
    clases = [
        (0, "alto", "Reglamentación"),
        (1, "ceda", "Reglamentación"),
        (2, "estacionamiento", "Reglamentación"),
        (3, "no_estacionamiento", "Reglamentación"),
        (4, "no_izquierda", "Reglamentación"),
        (5, "no_paso", "Reglamentación"),

        # Falta definir la clase 6
        # (6, "...", "Prevención"),

        (7, "peaton", "Prevención"),
        (8, "tren", "Prevención"),
        (9, "semaforo", "Prevención"),
        (10, "reductor", "Prevención"),
        (11, "escolar", "Prevención"),

        (12, "kilometro", "Información"),
        (13, "lugar", "Información"),
        (14, "gasolinera", "Información"),
    ]

    for codigo, nombre, categoria in clases:
        clase_existente = sesion.scalar(
            select(ClaseSenalBD).where(
                ClaseSenalBD.codigo == codigo
            )
        )

        if clase_existente is None:
            clase = ClaseSenalBD(
                codigo=codigo,
                nombre=nombre,
                categoria=categoria,
                activa=True
            )

            sesion.add(clase)

        else:
            clase_existente.nombre = nombre
            clase_existente.categoria = categoria
            clase_existente.activa = True

def ejecutar_seed():
    sesion = SessionLocal()

    try:
        crear_usuarios_iniciales(sesion)
        crear_clases_iniciales(sesion)

        sesion.commit()

        print("Datos iniciales creados correctamente.")

    except Exception:
        sesion.rollback()
        raise

    finally:
        sesion.close()


if __name__ == "__main__":
    ejecutar_seed()