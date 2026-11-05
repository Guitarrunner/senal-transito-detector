import json
import sqlite3
import time
import uuid

from pathlib import Path


class ColaLocal:

    def __init__(self, ruta=None):
        if ruta is None:
            raiz = Path(__file__).resolve().parents[2]
            ruta = raiz / "data" / "cola_local.sqlite3"

        self.ruta = Path(ruta).resolve()
        self.ruta.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with self._conectar() as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS pendientes (
                    id TEXT PRIMARY KEY,
                    usuario_id TEXT NOT NULL,
                    datos TEXT NOT NULL,
                    evidencia BLOB NOT NULL,
                    creado_en REAL NOT NULL,
                    intentos INTEGER NOT NULL DEFAULT 0,
                    proximo_intento REAL NOT NULL DEFAULT 0,
                    ultimo_error TEXT,
                    bloqueado INTEGER NOT NULL DEFAULT 0
                )
            """)

    def _conectar(self):
        conexion = sqlite3.connect(
            self.ruta,
            timeout=10
        )
        conexion.row_factory = sqlite3.Row
        return conexion

    def encolar(self, usuario_id, datos, evidencia_bytes):
        identificador = str(uuid.uuid4())

        with self._conectar() as conexion:
            conexion.execute(
                """
                INSERT INTO pendientes (
                    id,
                    usuario_id,
                    datos,
                    evidencia,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    identificador,
                    str(usuario_id),
                    json.dumps(datos),
                    evidencia_bytes,
                    time.time()
                )
            )

        return identificador

    def obtener_siguiente(self, usuario_id):
        with self._conectar() as conexion:
            fila = conexion.execute(
                """
                SELECT *
                FROM pendientes
                WHERE usuario_id = ?
                  AND bloqueado = 0
                  AND proximo_intento <= ?
                ORDER BY creado_en, id
                LIMIT 1
                """,
                (
                    str(usuario_id),
                    time.time()
                )
            ).fetchone()

        if fila is None:
            return None

        pendiente = dict(fila)
        pendiente["datos"] = json.loads(
            pendiente["datos"]
        )
        return pendiente

    def confirmar_envio(self, identificador):
        with self._conectar() as conexion:
            conexion.execute(
                "DELETE FROM pendientes WHERE id = ?",
                (identificador,)
            )

    def registrar_error(
        self,
        identificador,
        error,
        reintentable=True
    ):
        with self._conectar() as conexion:
            fila = conexion.execute(
                "SELECT intentos FROM pendientes WHERE id = ?",
                (identificador,)
            ).fetchone()

            if fila is None:
                return

            intentos = fila["intentos"] + 1

            espera = min(
                300,
                5 * (2 ** min(intentos - 1, 6))
            )

            conexion.execute(
                """
                UPDATE pendientes
                SET intentos = ?,
                    proximo_intento = ?,
                    ultimo_error = ?,
                    bloqueado = ?
                WHERE id = ?
                """,
                (
                    intentos,
                    time.time() + espera,
                    str(error),
                    int(not reintentable),
                    identificador
                )
            )

    def contar_pendientes(self, usuario_id):
        with self._conectar() as conexion:
            fila = conexion.execute(
                """
                SELECT COUNT(*) AS cantidad
                FROM pendientes
                WHERE usuario_id = ?
                """,
                (str(usuario_id),)
            ).fetchone()

        return fila["cantidad"]