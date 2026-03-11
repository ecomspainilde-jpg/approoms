# Routes / Pages

## Archivos HTML en `approoms/public/`

| Path | Descripción |
|------|-------------|
| `/` (index.html) | Redirect a 01-landing-page.html |
| `01-landing-page.html` | Landing page principal |
| `02-upload-wizard.html` | Wizard para subir foto y renderizar |
| `03-dashboard.html` | Dashboard del usuario con sus renders |
| `04-pago-bizum.html` | Página de pago con Bizum |
| `05-gracias.html` | Página de confirmación post-pago |
| `06-perfil-usuario.html` | Perfil de usuario |
| `07-consejos-decoracion.html` | Blog/Consejos de decoración |
| `08-estilo-moderno.html` | Galería estilo moderno |
| `09-estilo-nordico.html` | Galería estilo nórdico |
| `10-estilo-industrial.html` | Galería estilo industrial |
| `11-estilo-minimalista.html` | Galería estilo minimalista |
| `12-estilo-rustico.html` | Galería estilo rústico |
| `13-estilo-bohemio.html` | Galería estilo bohemio |
| `admin-dashboard.html` | Dashboard de admin |
| `blog-*.html` | Artículos del blog |
| `privacidad.html` | Política de privacidad |
| `terminos.html` | Términos y condiciones |

## Flujo de usuario típico

1. Landing → 02-upload-wizard → 04-pago-bizum → 05-gracias → 03-dashboard
2. Landing → 07-consejos-decoracion → blog posts
3. Landing/Dashboard → 06-perfil-usuario
