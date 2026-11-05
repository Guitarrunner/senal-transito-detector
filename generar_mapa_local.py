import argparse
import math
import sqlite3
from io import BytesIO
from pathlib import Path

import geopandas as gpd
from PIL import Image, ImageDraw
from shapely.geometry import box


# TkinterMapView usa este texto como clave en SQLite.
# No descargaremos imágenes de esa dirección.
SERVIDOR = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"

OESTE, SUR = -86.2, 8.0
ESTE, NORTE = -82.4, 11.4

ZOOM_MINIMO = 6
ZOOM_MAXIMO = 16

LIMITE_MERCATOR = 20037508.342789244
ESCALA = 2
TAMANO = 256


def coordenada_tesela(longitud, latitud, zoom):
    cantidad = 2 ** zoom

    x = (longitud + 180) / 360 * cantidad
    radianes = math.radians(latitud)

    y = (
        1 - math.asinh(math.tan(radianes)) / math.pi
    ) / 2 * cantidad

    return math.floor(x), math.floor(y)


def limites_tesela(x, y, zoom):
    lado = 2 * LIMITE_MERCATOR / (2 ** zoom)

    izquierda = -LIMITE_MERCATOR + x * lado
    arriba = LIMITE_MERCATOR - y * lado

    return (
        izquierda,
        arriba - lado,
        izquierda + lado,
        arriba
    )


def obtener_lineas(geometria):
    if geometria.is_empty:
        return

    if geometria.geom_type == "LineString":
        yield geometria

    elif hasattr(geometria, "geoms"):
        for parte in geometria.geoms:
            yield from obtener_lineas(parte)

def dibujar_bordes(
    dibujo,
    bordes,
    region,
    izquierda,
    arriba,
    factor,
    color,
    grosor
):
    for geometria in bordes:
        if geometria is None or geometria.is_empty:
            continue

        if not geometria.intersects(region):
            continue

        recorte = geometria.intersection(region)

        for linea in obtener_lineas(recorte):
            puntos = [
                (
                    (coordenada[0] - izquierda) * factor,
                    (arriba - coordenada[1]) * factor
                )
                for coordenada in linea.coords
            ]

            if len(puntos) >= 2:
                dibujo.line(
                    puntos,
                    fill=color,
                    width=grosor
                )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    argumentos = parser.parse_args()

    raiz = Path(__file__).resolve().parent
    destino = raiz / "data/mapas/costa_rica.sqlite3"
    destino.parent.mkdir(parents=True, exist_ok=True)

    print("Leyendo y proyectando calles...", flush=True)

    calles = gpd.read_file(
        argumentos.archivo,
        layer="gis_osm_roads_free",
        engine="pyogrio"
    ).to_crs(epsg=3857)

    calles = calles[
        calles.geometry.notna()
        & ~calles.geometry.is_empty
    ].reset_index(drop=True)

    indice = calles.sindex

    print("Leyendo límites terrestres...", flush=True)

    provincias = gpd.read_file(
        raiz / "data/mapas/provincias_cr.geojson"
    ).to_crs(epsg=3857)

    if len(provincias) != 7:
        raise ValueError(
            "Se esperaban siete provincias. "
            "Revisá la capa descargada."
        )

    provincias["geometry"] = (
        provincias.geometry.make_valid()
    )

    # Unir provincias elimina sus divisiones interiores
    # para obtener el contorno exterior del país.
    pais = provincias.dissolve()

    borde_nacional = pais.geometry.boundary
    bordes_provincias = provincias.geometry.boundary

    with sqlite3.connect(destino) as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS tiles (
                zoom INTEGER NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                server TEXT NOT NULL,
                tile_image BLOB NOT NULL,
                PRIMARY KEY (zoom, x, y, server)
            )
        """)

        for zoom in range(ZOOM_MINIMO, ZOOM_MAXIMO + 1):
            x_min, y_min = coordenada_tesela(
                OESTE, NORTE, zoom
            )

            x_max, y_max = coordenada_tesela(
                ESTE, SUR, zoom
            )

            total = (
                (x_max - x_min + 1)
                * (y_max - y_min + 1)
            )

            print(
                f"Zoom {zoom}: generando {total} teselas...",
                flush=True
            )

            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    izquierda, abajo, derecha, arriba = (
                        limites_tesela(x, y, zoom)
                    )

                    region = box(
                        izquierda, abajo, derecha, arriba
                    )

                    posiciones = indice.query(
                        region,
                        predicate="intersects"
                    )

                    imagen = Image.new(
                        "RGB",
                        (TAMANO * ESCALA, TAMANO * ESCALA),
                        "#f5f3ef"
                    )
                    dibujo = ImageDraw.Draw(imagen)

                    factor = (
                        TAMANO * ESCALA
                        / (derecha - izquierda)
                    )

                    for posicion in posiciones:
                        geometria = (
                            calles.geometry.iloc[int(posicion)]
                            .intersection(region)
                        )

                        for linea in obtener_lineas(geometria):
                            puntos = [
                                (
                                    (coordenada[0] - izquierda) * factor,
                                    (arriba - coordenada[1]) * factor
                                )
                                for coordenada in linea.coords
                            ]

                            if len(puntos) >= 2:
                                dibujo.line(
                                    puntos,
                                    fill="#777777",
                                    width=ESCALA
                                )

                    dibujar_bordes(
                        dibujo,
                        bordes_provincias,
                        region,
                        izquierda,
                        arriba,
                        factor,
                        color="#655070",
                        grosor=2 * ESCALA
                    )

                    dibujar_bordes(
                        dibujo,
                        borde_nacional,
                        region,
                        izquierda,
                        arriba,
                        factor,
                        color="#202020",
                        grosor=4 * ESCALA
                    )

                    imagen = imagen.resize(
                        (TAMANO, TAMANO),
                        Image.Resampling.LANCZOS
                    )

                    buffer = BytesIO()
                    imagen.save(buffer, format="PNG")

                    conexion.execute(
                        """
                        INSERT OR REPLACE INTO tiles
                            (zoom, x, y, server, tile_image)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            zoom,
                            x,
                            y,
                            SERVIDOR,
                            buffer.getvalue()
                        )
                    )

            conexion.commit()

    print(f"\nMapa generado: {destino}")


if __name__ == "__main__":
    main()