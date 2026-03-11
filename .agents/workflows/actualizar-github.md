---
description: Sincroniza los cambios locales con el repositorio de GitHub (add, commit y push).
---

Este workflow automatiza el proceso de subir los cambios al repositorio remoto.

1. Añadir todos los cambios al área de preparación (stage).
   // turbo
2. Confirmar los cambios con un mensaje (commit).
   // turbo
3. Subir los cambios a la rama principal en GitHub (push).

### Instrucciones para el Agente

Cuando el usuario pida "actualizar GitHub" o similar:

- Pregunta por el mensaje del commit si no se ha proporcionado uno descriptivo.
- Ejecuta los comandos en la raíz del repositorio (`c:\imf\habitacion\approoms`).
- Informa al usuario una vez completado.
