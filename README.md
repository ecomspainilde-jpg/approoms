# approoms

Aplicación de renderizado de interiores lista para despliegue en Google Cloud Run.

## Despliegue en Google Cloud Run

Esta aplicación está configurada para ser desplegada automáticamente mediante **Cloud Build Triggers** conectados a GitHub.

### Configuración de Variables de Entorno

Para que la aplicación funcione correctamente en Cloud Run, asegúrate de configurar las siguientes variables de entorno en la consola de Google Cloud:

1.  **`GCP_PROJECT_ID`**: El ID de tu proyecto de Google Cloud (ej: `gen-lang-client-0426824151`).
2.  **`GCP_LOCATION`**: La región de Vertex AI (por defecto `us-central1`).

### Infraestructura Requerida

- **Vertex AI API**: Debe estar habilitada en el proyecto.
- **Firebase**: Firestore y Cloud Storage deben estar configurados.
- **Cloud Run Service Account**: Debe tener permisos para usar Vertex AI y acceder a Firebase.
