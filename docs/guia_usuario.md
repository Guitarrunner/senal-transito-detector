# Guía de usuario

El sistema tiene una app de captura para iPhone y una interfaz de escritorio para Gestión. Para instalación y configuración, consultá la [guía técnica](guia_tecnica.md).

## Campo · Capturar desde el iPhone

1. Abrí **Señales Campo** e iniciá sesión con tu cuenta de Campo mientras el servidor esté accesible.
2. Permití cámara, ubicación durante el uso y acceso a la red local cuando el iPhone lo solicite.
3. Tocá **Iniciar cámara**, apuntá a la señal y esperá a que aparezcan la clase y la confianza.
4. Tocá **Capturar detección** y esperá a que se genere la evidencia. La app necesita una señal detectada y una lectura de ubicación reciente. Si aparece un aviso de ubicación, esperá una nueva lectura y repetí la captura.
5. Revisá **Última captura** y confirmá que la evidencia cubra los rostros o placas visibles. El tratamiento automático cubre las regiones que logra detectar.
6. Usá **Enviar pendientes** cuando tengas acceso a Gestión. **Revisar cola local** actualiza la lista de capturas de tu cuenta. Una captura puede contener varias señales y sale de la lista cuando se confirma el envío de todas.

Si perdés la conexión después de iniciar sesión, podés seguir capturando con la app abierta y la ubicación disponible. Las capturas pendientes se guardan en el teléfono. Al recuperar la conexión, podés enviarlas manualmente o dejar que la app reintente mientras esté activa. Si cerrás la app y tenés que iniciar sesión de nuevo, necesitás acceso a Gestión. El botón **Eliminar** borra de la cola la copia local de la captura seleccionada.

## Operador · Revisar e inventariar

1. Abrí Gestión e iniciá sesión como operador. Entrá a **Detecciones pendientes**.
2. Seleccioná una fila y revisá la clase, la confianza, la evidencia y la ubicación disponible.
3. Usá **Aprobar** si la detección corresponde a una señal válida, o **Rechazar** si la evidencia no la respalda.
4. Abrí **Inventario** para consultar la señal aprobada y sus detecciones asociadas. Seleccioná la señal para revisar su detalle.
5. Si corresponde un cambio de condición, seleccioná el nuevo estado y pulsá **Actualizar estado**. Confirmá el cambio en **Historial de estado**.
6. Abrí **Mapa** para consultar las señales que tienen coordenadas. Podés seleccionar un marcador para volver al detalle en el inventario. El punto indica dónde se realizó la captura.

## Administración · Usuarios, datasets y modelos

- **Usuarios.** Creá cuentas y asigná el rol de Campo, Operador o Administrador. Desde esta vista también podés activar o desactivar cuentas.
- **Dataset.** Seleccioná o creá un dataset, cargá imágenes y abrí una para etiquetarla. Dibujá un recuadro ajustado alrededor de cada señal visible que pertenezca al catálogo, elegí la clase y pulsá **Guardar anotación**. Revisá las anotaciones y las estadísticas antes de exportar.
- **Modelos.** En **Nuevo entrenamiento**, seleccioná el dataset y completá los parámetros. Pulsá **Iniciar entrenamiento** y consultá el progreso en **Entrenamientos**. En **Modelos entrenados**, seleccioná una versión y usá **Activar modelo seleccionado** cuando coincida con la versión instalada en el cliente. Activar una versión en Gestión no instala un paquete nuevo en el iPhone.

## Si algo falla

| Lo que ves | Qué revisar |
| --- | --- |
| El iPhone no inicia sesión | Comprobá que la Mac y el iPhone tengan acceso a la misma red, que la API esté corriendo y que la app tenga permiso de red local. |
| No se puede capturar | Revisá los permisos, esperá una lectura de ubicación reciente y confirmá que aparezca una detección en pantalla. |
| Hay capturas pendientes | Abrí el detalle del error en la cola y restablecé la conexión. Si el error menciona el modelo o una clase, avisá a Administración para revisar la versión activa o el catálogo. |
| No aparece una señal en el mapa | Confirmá que la detección esté aprobada, que la señal tenga coordenadas y que Gestión tenga instalada la base del mapa local. |
