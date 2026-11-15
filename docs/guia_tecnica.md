# Guía técnica

## Arquitectura y flujo

El iPhone adquiere cuadros con AVFoundation, ejecuta el detector mediante Vision y Core ML y recibe la ubicación de Core Location. Al capturar, la app cubre las regiones sensibles detectadas y guarda la evidencia JPEG junto con los metadatos en una cola local. Cada detección conserva su UUID en los reintentos. La API recibe el registro y persiste los metadatos en PostgreSQL y la evidencia en disco. La interfaz Tkinter consulta la API para revisar detecciones, mantener el inventario y mostrar el mapa.

| Responsabilidad | Referencia en el código |
| --- | --- |
| Cámara, ubicación y anonimización móvil | `CamaraIOS.swift`, `UbicacionIOS.swift`, `AnonimizadorIOS.swift` |
| Sesión, cola y transmisión móvil | `SesionAPI.swift`, `ColaLocalIOS.swift`, `EnvioDeteccionesIOS.swift` |
| API y persistencia | `src/gestion/main.py`, `src/gestion/routers/`, `src/gestion/modelos.py`, `migrations/` |
| Escritorio | `src/main.py`, `src/ui/interfaz_gestion.py`, `src/ui/interfaz_visualizacion.py` |
| Dataset y entrenamiento | `src/gestion/servicios/exportacion_yolo.py`, `src/gestion/servicios/entrenamiento_modelo.py` |

## Servidor y escritorio

Usá Python 3.10 o posterior con Tk disponible, Docker Compose para PostgreSQL 16 o una instancia de PostgreSQL equivalente, y acceso a la red local para las pruebas móviles. En macOS, `python3 -m tkinter` sirve para comprobar que la instalación de Python puede abrir la interfaz.

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Creá un archivo `.env` en la raíz y reemplazá los valores de ejemplo. Para `DATABASE_URL`, usá la misma cuenta y puerto que configuraste en PostgreSQL. Si la contraseña contiene caracteres reservados de una URL, codificalos en ese valor.

```dotenv
POSTGRES_DB=senal_transito
POSTGRES_USER=senal_app
POSTGRES_PASSWORD=REEMPLAZAR_PASSWORD_BD
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://senal_app:REEMPLAZAR_PASSWORD_BD@127.0.0.1:5432/senal_transito

JWT_SECRET_KEY=REEMPLAZAR_CLAVE_ALEATORIA
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
GESTION_API_URL=http://127.0.0.1:8000

SEED_ADMIN_PASSWORD=REEMPLAZAR_PASSWORD_ADMIN
SEED_OPERADOR_PASSWORD=REEMPLAZAR_PASSWORD_OPERADOR
SEED_CAMPO_PASSWORD=REEMPLAZAR_PASSWORD_CAMPO

DATASET_STORAGE_DIR=data/datasets
YOLO_EXPORT_DIR=exports
EVIDENCE_STORAGE_DIR=data/evidence
```

Definí `DATASET_STORAGE_DIR` explícitamente. En el código revisado, la carga de imágenes y la exportación usan valores por defecto distintos. En una instalación existente, mantené la ruta donde ya se guardan las imágenes. Guardá el `.env` con las credenciales fuera de Git.

```bash
docker compose up -d db
docker compose ps
```

Cuando PostgreSQL esté listo, ejecutá las migraciones. En una base **nueva y vacía**, ejecutá también el seed para crear las cuentas `admin`, `operador` y `campo` y poblar el catálogo.

```bash
python -m alembic upgrade head
python -m src.gestion.seed
```

En una base existente, revisá `src/gestion/seed.py` antes de volver a ejecutarlo. En `38b88e9`, el seed actualiza clases por código y puede renombrar registros con anotaciones o detecciones asociadas. Para el catálogo de trabajo, conservá los IDs existentes y los códigos `lugar=13`, `bici=15` e `interseccion=16`. Ajustá el seed para buscar primero por nombre e insertar únicamente clases faltantes con códigos libres.

Iniciá el servidor. En otra terminal, desde la raíz y con el entorno activo, ejecutá `python -m src.main`.

```bash
python -m uvicorn src.gestion.main:app --host 0.0.0.0 --port 8000
```

Abrí `http://127.0.0.1:8000/docs` para consultar el contrato de la API. Los puntos principales son `/auth/login`, `/clases`, `/modelos/activo`, `/detecciones`, `/senales`, `/datasets` y `/usuarios`. Las operaciones de Gestión requieren una cuenta con el rol correspondiente.

## Cliente iOS

1. Abrí ios/senalesCampo/senalesCampo.xcodeproj con Xcode 27.2, la versión con la que se verificó la apertura del proyecto. La configuración compartida se encuentra en project.xcproj. Seleccioná el esquema SenalesCampo y configurá el equipo de firma para tu dispositivo.
2. Abrí `senalesCampo.xcodeproj` en Xcode. Configurá el equipo de firma para tu iPhone y verificá los permisos de cámara, ubicación durante el uso y red local.
3. En `SenalesCampo/Info.plist`, configurá `APIBaseURL` con la dirección de la Mac en la red local, por ejemplo `http://192.168.1.10:8000`. Conectá el iPhone y la Mac a una red desde la que el teléfono pueda alcanzar ese servidor.
4. Verificá que `senales_v1_0.mlpackage`, `rostros_ios.mlpackage` y `placas_ios.mlpackage` estén incluidos en el target `SenalesCampo`. Seleccioná el iPhone físico e instalá la app con **⌘R**.
5. En **Administración → Modelos**, activá la versión correspondiente al paquete. El cliente contrasta la versión guardada en una captura nueva con `/modelos/activo` antes del envío.

Las migraciones y el seed preparan la base de datos para una instalación nueva. Para enviar detecciones con el modelo senales_v1_0.mlpackage, Gestión requiere que la versión v1.0 esté registrada y activa. La restauración de los datos de prueba y el registro de la v1.0 desde una instalación limpia quedaron pendientes de verificación.

## Dataset y actualización del modelo

Gestión exporta imágenes y etiquetas en particiones `train`, `val` y `test`. La exportación deriva las clases de las anotaciones y genera índices YOLO consecutivos. Los índices de YOLO se conservan junto al peso entrenado. En el envío móvil, la etiqueta se resuelve por nombre en `/clases` para obtener el ID de PostgreSQL.

El orden confirmado para la v1.0 es:

```yaml
names:
  0: alto
  1: ceda
  2: estacionamiento
  3: no_estacionamiento
  4: no_izquierda
  5: no_paso
  6: peaton
  7: tren
  8: semaforo
  9: reductor
  10: escolar
  11: lugar
  12: bici
  13: interseccion
```

El `dataset/dataset.yaml` de `38b88e9` corresponde a un catálogo anterior de 15 clases. Usá el YAML generado para el entrenamiento v1.0 y su par de imágenes y etiquetas. Conservá las particiones por señal física para evitar que fotos de la misma señal se repartan entre entrenamiento y prueba.

Para reproducir la exportación móvil, usá en macOS el entorno de exportación con Ultralytics y Core ML Tools:

```bash
yolo export model="/ruta/al/best.pt" format=coreml imgsz=640 batch=1 nms=True
```

Al cambiar de versión, actualizá el paquete incluido en el target, el recurso que carga `CamaraIOS.swift` y la versión que guarda `ContentView.swift`. Activá en Gestión esa misma versión y probá una detección nueva antes de retirar el paquete anterior. Los registros pendientes conservan la versión original.

1. Incorporar al target SenalesCampo el paquete Core ML de la versión que se va a instalar.
2. Actualizar en CamaraIOS.swift el nombre del recurso que carga Vision y en ContentView.swift la versión que se registra en las capturas nuevas.
3. Compilar e instalar la aplicación actualizada en el iPhone.
4. Activar esa misma versión en Administración → Modelos y comprobar que GET /modelos/activo devuelve la versión esperada.
5. Con la app abierta, realizar una captura nueva y verificar en Gestión que la detección se recibió con la versión correcta. Los registros pendientes conservan la versión con la que se generaron.

## Mapa local

Gestión utiliza una base SQLite de teselas que se genera localmente. La interfaz busca el archivo en `data/mapas/costa_rica.sqlite3`.

### Insumos cartográficos

| Insumo | Preparación |
|---|---|
| Red vial de Costa Rica | Descargá el [extracto GeoPackage de Geofabrik](https://download.geofabrik.de/central-america/costa-rica.html) y descomprimí el archivo `.gpkg.zip`. El archivo `.gpkg` debe contener la capa `gis_osm_roads_free`. |
| Límites provinciales | Descargá el GeoJSON de la [capa CRI ADM1 de geoBoundaries](https://www.geoboundaries.org/api/current/gbOpen/CRI/ADM1/) y guardalo como `data/mapas/provincias_cr.geojson`. El generador busca este archivo en esa ruta. |
| Límites cantonales | Descargá el GeoJSON de la [capa CRI ADM2 de geoBoundaries](https://www.geoboundaries.org/api/current/gbOpen/CRI/ADM2/) y guardalo como `data/mapas/cantones_cr.geojson`. Este archivo se pasa al generador mediante `--cantones`. |

### Generación de la base SQLite

Desde la raíz del repositorio, con el entorno virtual activo, instalá las dependencias y ejecutá el generador. Sustituí `/ruta/al/costa-rica.gpkg` por la ruta del archivo descomprimido.

```bash
python -m pip install geopandas shapely pyogrio pillow

python generar_mapa_local.py "/ruta/al/costa-rica.gpkg" \
  --cantones data/mapas/cantones_cr.geojson \
  --zoom-maximo 16 \
  --salida data/mapas/costa_rica.sqlite3
```

El comando genera teselas hasta el nivel 16, que coincide con el zoom máximo configurado en Gestión. Una vez generada la base, abrí **Gestión → Mapa** y comprobá que se muestren la red vial y los límites provinciales. Acercá el mapa para verificar los límites y nombres cantonales.

Para documentar la regeneración, registrá el nombre y la fecha del extracto de Geofabrik, las versiones de las capas de geoBoundaries y el comando utilizado.

Las fuentes cartográficas son OpenStreetMap, mediante el extracto GeoPackage de Costa Rica distribuido por Geofabrik, y las capas CRI ADM1 y CRI ADM2 de geoBoundaries. Para cada regeneración se registrará el nombre y la fecha del extracto, la versión o fecha de descarga de los GeoJSON y el comando utilizado. Al compartir la base SQLite o las teselas, se conservarán las atribuciones de las fuentes y se revisarán sus condiciones de distribución.

## Comprobación de una instalación

1. Abrí la API y Gestión. Confirmá el acceso con una cuenta de operador y que el mapa local se muestre.
2. Instalá el cliente móvil, iniciá sesión como Campo y capturá una señal con una lectura de ubicación válida.
3. Probá una interrupción de conexión y el envío posterior. Verificá que cada detección se registre una sola vez.
4. Confirmá en Gestión la clase, la ubicación y la evidencia, aprobá la detección y buscá la señal en inventario y mapa.
5. Conservá el commit, la versión del modelo, las versiones del entorno y los recursos de prueba para poder repetir el recorrido.
