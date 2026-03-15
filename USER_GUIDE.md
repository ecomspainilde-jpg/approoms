# Guía de Usuario - RenderRoom

Bienvenido a RenderRoom, un generador de interiores hiperrealistas impulsado por IA. Esta guía te orientará en el uso de la aplicación.

## 1. Interfaz Principal (Navegación)

RenderRoom cuenta con un flujo paso a paso:

- Empieza en la página inicial (Landing Page) para conocer nuestros servicios.
- Procede al Asistente de Subida (Paso 1, `Upload Wizard`) para interactuar con la IA de RenderRoom.

## 2. Generar el Diseño de tu Habitación

En el Paso 1 (`Upload Wizard`), visualizarás una zona para subir/arrastrar tu foto actual, y directamente debajo una zona para describir cómo deseas la habitación de tus sueños con herramientas de IA:

1. Navega hasta la ventana de "Describe la habitación de tus sueños", e introduce texto describiendo claramente tu idea (ej: "Un estudio moderno con iluminación natural abundante y toques minimalistas").
2. Haz clic en el botón "Simular Pago y Generar".

## 3. Simulación de Pago

- Una vez haces clic, el sistema simula automáticamente una transacción (por el valor de 1 EUR/2.50 EUR de manera figurada).
- Podrás ver el estado del progreso en vivo bajo la sección "Resultado". Si el pago falla (para efectos de probar errores, se puede modificar el botón en el código base), el sistema retendrá la generación de la IA e indicará que el pago es requerido.
- Si la simulación del pago es un éxito, la instrucción se manda a los servidores de Vertex AI inmediatamente.

## 4. Obtener Resultados del Render

- Tras unos segundos de espera para que la IA procese la llamada a Vertex AI `gemini-2.0-flash-exp` e `imagen-3.0-generate-001`, se desplegará una respuesta.
- Bajo la misma pestaña de "Resultados", obtendrás la descripción final de tu habitación directamente traída de Vertex AI ("Final render of the improved room interior").
- Esta se mostrará fluidamente en tu pantalla sin cambiar ninguna otra interfaz de Google Stitch.

## ¡Disfruta de RenderRoom!

Con estos sencillos pasos ya estarás aprovechando los modelos fundacionales para visualizar interiores totalmente nuevos.
