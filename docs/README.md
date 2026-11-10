# Sistema de reconocimiento automático de señales de tránsito

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

La documentación toma como base el commit `38b88e9`. Ese commit incluye `senales_v1_0.mlpackage` y registra las capturas como v1.0. El proyecto compartido de Xcode, el mapa local y los datos de entrenamiento deben completarse según la [guía técnica](docs/guia_tecnica.md). La prueba de extremo a extremo requiere que la API tenga activa la versión correspondiente al modelo instalado.

El detector v1.0 reconoce 14 clases. La posición de un punto en el mapa corresponde al lugar de captura del iPhone. La inferencia puede continuar tras perder la conexión si la sesión ya está iniciada. El inicio de sesión y la sincronización requieren acceso a Gestión.
