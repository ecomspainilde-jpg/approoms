# RenderRoom - Site Vision & Roadmap

## Project Overview
**RenderRoom** es una aplicación web de renderizado de interiores con IA. Los usuarios suben fotos de sus habitaciones y reciben renders profesionales en diferentes estilos de decoración por solo 2,50€.

**Stitch Project ID:** 10149300038889827122

---

## 1. Site Vision

 democratizar el diseño de interiores permitiendo a cualquier persona obtener renders profesionales de sus habitaciones mediante IA. La experiencia debe ser premium, accesible y aspiracional.

---

## 2. User Flow

```
Landing → Upload Wizard → Dashboard → Render Generation → Payment → Results
```

---

## 3. Technology Stack

- **Frontend:** HTML + Tailwind CSS + Firebase SDK
- **Backend:** Python Flask + Vertex AI (Gemini 2.5, Imagen 3.0/4.0)
- **Storage:** Firebase Cloud Storage + Firestore
- **Deployment:** Google Cloud Run

---

## 4. Sitemap (Existing Pages)

| Page | File | Status |
|------|------|--------|
| Landing Page | `01-landing-page.html` | ✅ |
| Upload Wizard | `02-upload-wizard.html` | ✅ |
| Dashboard | `03-dashboard.html` | ✅ |
| Payment (Bizum) | `04-pago-bizum.html` | ✅ |
| Thank You | `05-gracias.html` | ✅ |
| User Profile | `06-perfil-usuario.html` | ✅ |
| Blog/Consejos | `07-consejos-decoracion.html` | ✅ |
| Estilo Moderno | `08-estilo-moderno.html` | ✅ |
| Estilo Nórdico | `09-estilo-nordico.html` | ✅ |
| Estilo Industrial | `10-estilo-industrial.html` | ✅ |
| Estilo Minimalista | `11-estilo-minimalista.html` | ✅ |
| Estilo Rústico | `12-estilo-rustico.html` | ✅ |
| Estilo Bohemio | `13-estilo-bohemio.html` | ✅ |
| Admin Dashboard | `admin-dashboard.html` | ✅ |
| Términos | `terminos.html` | ✅ |
| Privacidad | `privacidad.html` | ✅ |

---

## 5. Roadmap (Pending)

- [ ] Página de FAQ
- [ ] Página de contacto
- [ ] Tutorial de uso
- [ ] Página de precios detallada
- [ ] Integración con Stripe real

---

## 6. Creative Freedom (Ideas)

- [ ] Landing page alternativa con más hero visual
- [ ] Página "Cómo funciona" detallada
- [ ] Galería de inspiración por habitaciones
- [ ] Calculador de presupuesto de decoración
- [ ] Test de estilo de decoración (quiz interactivo)
- [ ] Página de testimonios/reviews

---

## 7. Styles Available

1. **Moderno** - Contemporáneo, líneas limpias
2. **Nórdico** - Escandinavo, hygge, luz natural
3. **Industrial** - Urbano, ladrillo, metal
4. **Minimalista** - Monocromático, esencial
5. **Rústico** - Farmhouse, materiales naturales
6. **Bohemio** - Ecléctico, textiles, plantas
