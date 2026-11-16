# Sistema de Reconocimiento Automático de Señales de Tránsito Mediante Visión por Computadora sobre una Plataforma de Captura y Procesamiento en el Edge


Trabajo Final de Graduación de Josué Araya García, Ingeniería en Computadores, Tecnológico de Costa Rica. El prototipo captura señales de tránsito en un iPhone, ejecuta un detector YOLO en el dispositivo y envía detecciones con evidencia anonimizada a un sistema de revisión e inventario.

## Componentes

| Componente | Ubicación | Responsabilidad |
| --- | --- | --- |
| Señales Campo | `ios/senalesCampo/SenalesCampo/` | Cámara, inferencia con Core ML y Vision, ubicación, anonimización y cola de envío. |
| API de Gestión | `src/gestion/` | Autenticación, catálogo, detecciones, inventario, datasets y versiones del detector. |
| Gestión de escritorio | `src/ui/` | Revisión de detecciones, inventario, mapa y administración. Se inicia con `python -m src.main`. |
| Persistencia | `docker-compose.yml`, `migrations/` | PostgreSQL y migraciones de esquema con Alembic. |

## Instalación y uso

1. Seguí la [guía técnica](docs/guia_tecnica.md) para configurar Python, PostgreSQL y las cuentas iniciales.
2. Desde la raíz del repositorio, con el entorno virtual activo, iniciá la API y abrí Gestión en otra terminal.

   ```bash
   python -m uvicorn src.gestion.main:app --host 0.0.0.0 --port 8000
   ```

   ```bash
   python -m src.main
   ```

3. Para captura móvil, configurá el proyecto compartido en Xcode, apuntá `APIBaseURL` al servidor en tu red local e instalá la app en un iPhone físico. La [guía de usuario](docs/guia_usuario.md) describe el flujo por rol.

## Versión de referencia

La entrega documentada en el informe corresponde al commit `8022a7f09daad08d7be1cfefc837681001511987`. Esta revisión identifica el código y la documentación de referencia. El commit exacto utilizado durante el entrenamiento de v1.0 quedó sin confirmar.

El repositorio incluye el proyecto compartido `ios/senalesCampo/senalesCampo.xcodeproj/` y el detector `senales_v1_0.mlpackage`. Se verificó que Xcode 27.2 reconociera el proyecto local y el esquema `SenalesCampo`.

El mapa local se genera siguiendo la [guía técnica](docs/guia_tecnica.md). Los datos y archivos del entrenamiento deben estar disponibles según el procedimiento de entrega documentado. La instalación completa desde un entorno limpio quedó pendiente de verificación.

Para enviar detecciones, la versión activa en Gestión debe corresponder al modelo instalado en el iPhone. La sustitución del modelo móvil se realiza manualmente mediante la incorporación del paquete Core ML, la actualización de sus referencias y la compilación e instalación de la aplicación.

## Alcance y condiciones de operación

El detector v1.0 reconoce 14 clases de señales de tránsito. La ubicación asociada a una detección corresponde a una lectura de posición del teléfono y puede diferir de la ubicación física de la señal.

El inicio de sesión requiere acceso al servidor. Con la sesión iniciada, la aplicación puede continuar capturando y ejecutando inferencias durante una interrupción de conectividad, conservando las capturas seleccionadas en una cola local. La sincronización requiere que el servidor sea accesible y que la aplicación esté activa.

La anonimización se aplica antes de guardar la evidencia en la cola. Su cobertura depende de los modelos de detección de rostros y placas. Durante las pruebas se observaron ocultamientos incorrectos de partes de algunas señales.

Las métricas de detección se obtuvieron con `best.pt` mediante Ultralytics. El rendimiento móvil se midió con el modelo exportado a Core ML. La equivalencia de predicciones entre ambos artefactos quedó pendiente de verificación.
