# Pages Dependency Trees

Este es un proyecto de HTML estático. Cada página es un archivo independiente que incluye:
- Tailwind CSS (CDN)
- Google Fonts
- Material Symbols
- Firebase SDK
- CSS embebido en `<style>`
- JS embebido en `<script>`

No hay imports entre páginas - cada HTML es autosuficiente.

## Archivos principales

### Landing Page
- Entry: `approoms/public/01-landing-page.html`
- Dependencias: Solo Tailwind CDN + Google Fonts + Firebase

### Dashboard
- Entry: `approoms/public/03-dashboard.html`
- Dependencias: Solo Tailwind CDN + Google Fonts + Firebase

### Perfil Usuario
- Entry: `approoms/public/06-perfil-usuario.html`
- Dependencias: Solo Tailwind CDN + Google Fonts + Firebase

### Upload Wizard
- Entry: `approoms/public/02-upload-wizard.html`
- Dependencias: Solo Tailwind CDN + Google Fonts + Firebase

## Recursos Compartidos (CDN)
- https://cdn.tailwindcss.com?plugins=forms,container-queries
- https://fonts.googleapis.com/css2?family=Inter:wght@100..900
- https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined
- Firebase SDK 10.8.0
