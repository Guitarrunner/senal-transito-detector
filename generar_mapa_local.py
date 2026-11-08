import argparse
import math
import sqlite3
from collections import defaultdict
from contextlib import closing, contextmanager
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import geopandas as gpd
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box


# TkinterMapView usa este texto como clave en SQLite.
# No descargaremos imágenes de esa dirección.
SERVIDOR = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"

OESTE, SUR = -86.2, 8.0
ESTE, NORTE = -82.4, 11.4

ZOOM_MINIMO = 6
ZOOM_MAXIMO = 16
ZOOM_BORDES_CANTONALES = 9
ZOOM_NOMBRES_CANTONALES = 11

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

def columna_nombre(capa):
    columnas = {columna.lower(): columna for columna in capa.columns}
    for nombre in ("shapename", "nombre", "name"):
        if nombre in columnas:
            return columnas[nombre]
    raise ValueError("No se encontró una columna con los nombres de la capa.")


def preparar_cantones(ruta, provincias):
    cantones = gpd.read_file(ruta).to_crs(epsg=3857)
    if cantones.empty:
        raise ValueError("La capa de cantones está vacía.")

    cantones["geometry"] = cantones.geometry.make_valid()
    nombre_canton = columna_nombre(cantones)
    nombre_provincia = columna_nombre(provincias)
    etiquetas = []

    for _, canton in cantones.iterrows():
        geometria = canton.geometry
        if geometria is None or geometria.is_empty or geometria.area <= 0:
            raise ValueError("La capa contiene un cantón sin superficie válida.")

        # La mayor área de intersección evita depender de nombres coincidentes.
        areas = provincias.geometry.intersection(geometria).area
        if areas.max() <= 0:
            raise ValueError(f"No se pudo asociar {canton[nombre_canton]} a una provincia.")

        provincia = provincias.loc[areas.idxmax(), nombre_provincia]
        nombre = canton[nombre_canton]
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("Se encontró un cantón sin nombre.")
        if not isinstance(provincia, str) or not provincia.strip():
            raise ValueError(f"La provincia de {nombre} no tiene nombre.")

        punto = geometria.representative_point()
        etiquetas.append((geometria.area, punto, f"{nombre.strip()} - {provincia.strip()}"))

    return cantones.geometry.boundary.reset_index(drop=True), etiquetas


def fuente_cantones():
    for nombre in ("Arial.ttf", "DejaVuSans.ttf",
                   "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(nombre, size=11 * ESCALA)
        except OSError:
            pass
    return ImageFont.load_default(size=11 * ESCALA)


def etiquetas_por_tesela(etiquetas, zoom, fuente):
    # Coordenadas de píxeles globales: una etiqueta puede ocupar varias teselas.
    lado = TAMANO * ESCALA
    factor = lado * (2 ** zoom) / (2 * LIMITE_MERCATOR)
    trazo = ESCALA
    cajas = []
    por_tesela = defaultdict(list)

    for _, punto, texto in sorted(etiquetas, key=lambda dato: -dato[0]):
        x = round((punto.x + LIMITE_MERCATOR) * factor)
        y = round((LIMITE_MERCATOR - punto.y) * factor)
        izq, sup, der, inf = fuente.getbbox(
            texto, anchor="mm", stroke_width=trazo
        )
        caja = box(x + izq - trazo, y + sup - trazo,
                   x + der + trazo, y + inf + trazo)
        if any(caja.intersects(otra) for otra in cajas):
            continue
        cajas.append(caja)
        x1, y1, x2, y2 = caja.bounds
        for tx in range(math.floor(x1 / lado), math.floor(x2 / lado) + 1):
            for ty in range(math.floor(y1 / lado), math.floor(y2 / lado) + 1):
                por_tesela[tx, ty].append((x - tx * lado, y - ty * lado, texto))

    return por_tesela


@contextmanager
def construir_base(destino):
    # El visor conserva la base anterior hasta que se completa la nueva.
    with TemporaryDirectory(prefix="mapa-", dir=destino.parent) as temporal:
        base_temporal = Path(temporal) / destino.name
        with closing(sqlite3.connect(base_temporal)) as conexion:
            yield conexion
            conexion.commit()
        base_temporal.replace(destino)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("--cantones", type=Path, help="Capa GeoJSON CRI ADM2")
    parser.add_argument("--salida", type=Path, help="Ruta de la base SQLite")
    parser.add_argument(
        "--zoom-maximo", type=int, default=ZOOM_MAXIMO,
        choices=range(ZOOM_MINIMO, ZOOM_MAXIMO + 1)
    )
    argumentos = parser.parse_args()

    raiz = Path(__file__).resolve().parent
    destino = argumentos.salida or raiz / "data/mapas/costa_rica.sqlite3"
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

    bordes_cantones, nombres_cantones, indice_cantones, fuente = (), (), None, None
    if argumentos.cantones:
        print("Preparando cantones y etiquetas...", flush=True)
        bordes_cantones, nombres_cantones = preparar_cantones(
            argumentos.cantones, provincias
        )
        indice_cantones = bordes_cantones.sindex
        fuente = fuente_cantones()

    with construir_base(destino) as conexion:
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

        for zoom in range(ZOOM_MINIMO, argumentos.zoom_maximo + 1):
            etiquetas = (
                etiquetas_por_tesela(nombres_cantones, zoom, fuente)
                if fuente and zoom >= ZOOM_NOMBRES_CANTONALES else {}
            )
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

                    if indice_cantones is not None and zoom >= ZOOM_BORDES_CANTONALES:
                        indices = indice_cantones.query(region, predicate="intersects")
                        dibujar_bordes(
                            dibujo, bordes_cantones.iloc[indices], region,
                            izquierda, arriba, factor, "#772110", 3*ESCALA
                        )

                    dibujar_bordes(
                        dibujo,
                        bordes_provincias,
                        region,
                        izquierda,
                        arriba,
                        factor,
                        color="#6C2393",
                        grosor=5 * ESCALA
                    )

                    dibujar_bordes(
                        dibujo,
                        borde_nacional,
                        region,
                        izquierda,
                        arriba,
                        factor,
                        color="#202020",
                        grosor=7 * ESCALA
                    )

                    for px, py, texto in etiquetas.get((x, y), ()):
                        dibujo.text(
                            (px, py), texto, font=fuente, anchor="mm",
                            fill="#34283d", stroke_width=ESCALA,
                            stroke_fill="#ffffff"
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