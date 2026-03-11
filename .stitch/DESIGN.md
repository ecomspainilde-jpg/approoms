# Design System: RenderRoom - Renders de Habitaciones por 2,50€

**Project ID:** 10149300038889827122

## 1. Visual Theme & Atmosphere

RenderRoom encarna un **oasis tecnológico cálido y aspiracional**, donde la sofisticación del diseño de interiores se encuentra con la accesibilidad de un servicio al alcance de todos. La interfaz transmite una sensación de **lujo democrático** – renders profesionales de habitaciones a un precio irresistible: solo 2,50€ (1€ menos que un perrito caliente).

El ambiente visual es **envolvente y cinematográfico**, evocando la experiencia de hojear una revista de interiorismo de alta gama. El diseño utiliza fondos oscuros elegantes con acentos cálidos y luminosos que crean una atmósfera nocturna y premium, como entrar en un estudio de diseño exclusivo.

**Características Clave:**

- Modo oscuro sofisticado con toques dorados cálidos que transmiten premium
- Fotografías de habitaciones renderizadas como protagonistas absolutas
- Glassmorphism sutil en tarjetas y paneles para profundidad etérea
- Micro-animaciones fluidas que dan vida a la interfaz
- Tipografía moderna y limpia que respira elegancia
- Sensación de "antes y después" que genera WOW instantáneo
- Precio destacado de forma audaz: **2,50€** como heroico punto de conversión

## 2. Color Palette & Roles

### Primary Foundation

- **Noche Profunda** (#0D1117) – Color de fondo principal. Un negro azulado profundo que crea un lienzo cinematográfico y premium, evocando la sensación de un estudio de diseño nocturno.
- **Carbón Suave** (#161B22) – Superficie secundaria para tarjetas y paneles. Proporciona separación visual sutil sobre el fondo principal manteniendo la estética nocturna.
- **Obsidiana Cálida** (#1C2333) – Tercer nivel de superficie para elementos elevados, tooltips y menús desplegables.

### Accent & Interactive

- **Ámbar Dorado Brillante** (#F0A500) – Acento primario usado exclusivamente para CTAs principales ("Renderiza Ahora", "Subir Foto"), precios, estados activos e indicadores de progreso. Evoca calidez, creatividad y valor premium.
- **Ámbar Incandescente** (#FFB830) – Variante más clara del acento para hovers y estados de interacción, creando un efecto de "iluminación" cálida.
- **Violeta Eléctrico Profundo** (#7C3AED) – Acento secundario para elementos de IA/tecnología, badges de "Powered by AI" y efectos de gradiente que transmiten innovación.

### Typography & Text Hierarchy

- **Blanco Lunar** (#E6EDF3) – Texto principal para titulares y contenido destacado. Blanco suavizado que evita la dureza del blanco puro sobre fondos oscuros.
- **Plata Nebulosa** (#8B949E) – Texto secundario para descripciones, metadata y texto de soporte.
- **Gris Estelar** (#484F58) – Texto terciario para bordes, separadores y elementos estructurales ultra-sutiles.

### Functional States

- **Esmeralda Éxito** (#2EA043) – Render completado, confirmaciones, estados positivos
- **Coral Alerta** (#F85149) – Errores de subida, estados críticos, advertencias
- **Zafiro Info** (#58A6FF) – Información del sistema, tips, mensajes neutrales

## 3. Typography Rules

**Primary Font Family:** Inter
**Character:** Tipografía sans-serif geométrica y versátil con excelente legibilidad en interfaces oscuras. Formas limpias y neutrales que transmiten modernidad y profesionalismo.

### Hierarchy & Weights

- **Display Headlines (H1):** Bold weight (700), tracking suelto (0.02em), 3-4rem. Usado para hero sections como "Renders de Habitaciones por solo 2,50€".
- **Section Headers (H2):** Semi-bold weight (600), tracking sutil (0.01em), 2-2.5rem. Define zonas de contenido como "Cómo Funciona", "Galería de Resultados".
- **Subsection Headers (H3):** Medium weight (500), tracking normal, 1.5-1.75rem. Títulos de tarjetas de estilos, pasos del proceso.
- **Body Text:** Regular weight (400), line-height relajado (1.7), 1rem. Descripciones de servicios y texto informativo.
- **Price Display:** Extra-bold weight (800), 2.5-3rem, color Ámbar Dorado. El precio "2,50€" siempre prominente.
- **CTA Buttons:** Semi-bold weight (600), tracking sutil (0.02em), 1rem. Presencia equilibrada y llamativa.

### Spacing Principles

- Titulares usan tracking expandido para elegancia refinada
- Texto corporal mantiene line-height generoso (1.7) para lectura cómoda
- Ritmo vertical consistente con 2-3rem entre bloques de texto relacionados
- Márgenes amplios (5-8rem) entre secciones principales para respiración dramática

## 4. Component Stylings

### Buttons

- **Shape:** Esquinas generosamente redondeadas (12px/0.75rem) – modernas, amigables y premium
- **Primary CTA:** Gradiente de Ámbar Dorado a Ámbar Incandescente (#F0A500 → #FFB830), texto Noche Profunda (#0D1117), padding cómodo (1rem vertical, 2.5rem horizontal)
- **Hover State:** Brillo intensificado con sutil efecto de glow dorado, transición suave de 300ms ease-out
- **Focus State:** Anillo exterior en Ámbar Dorado con offset para accesibilidad de teclado
- **Secondary CTA:** Borde 1.5px en Ámbar Dorado, fondo transparente, hover rellena con tinte ámbar translúcido (rgba(240,165,0,0.1))
- **AI Action Button:** Gradiente sutil de Violeta Eléctrico a Ámbar (#7C3AED → #F0A500), efecto shimmer animado

### Cards & Render Containers

- **Corner Style:** Esquinas suavemente redondeadas (16px/1rem) creando bordes refinados y modernos
- **Background:** Carbón Suave (#161B22) con borde hairline de Gris Estelar (1px solid rgba(72,79,88,0.3))
- **Shadow Strategy:** Sombra difusa sutil por defecto (`0 4px 20px rgba(0,0,0,0.3)`). En hover, elevación dramática con glow ámbar (`0 8px 32px rgba(240,165,0,0.15)`)
- **Glassmorphism:** Backdrop-filter blur(12px) con fondo semi-transparente rgba(22,27,34,0.8) para paneles flotantes
- **Internal Padding:** Generoso 2rem creando espacio de respiración para el contenido
- **Image Treatment:** Bordes redondeados superiores, ratio 16:9 para renders, efecto de parallax sutil en scroll

### Before/After Slider

- **Estilo:** Slider interactivo con línea divisoria en Ámbar Dorado (2px)
- **Handle:** Círculo con fondo Ámbar, icono de flechas bidireccionales, sombra suave
- **Labels:** "Antes" y "Después" en badges glassmorphism semi-transparentes
- **Animación:** Movimiento suave con spring physics en arrastre

### Navigation

- **Style:** Barra horizontal fija con fondo glassmorphism (Noche Profunda al 85% + blur)
- **Typography:** Medium weight (500), 0.875rem, tracking expandido (0.04em) para sofisticación refinada
- **Default State:** Texto Plata Nebulosa
- **Active/Hover State:** Transición suave 200ms a Ámbar Dorado con underline animado
- **Logo:** "RenderRoom" con icono de habitación estilizado, gradiente ámbar
- **Mobile:** Menú hamburguesa elegante con drawer desde la derecha, overlay oscuro

### Upload Zone

- **Estilo:** Zona dropzone con borde dashed 2px en Gris Estelar, esquinas redondeadas (16px)
- **Hover/Drag:** Borde se ilumina en Ámbar Dorado, fondo se aclara sutilmente, icono de cámara pulsa
- **Activo:** Efecto de glow periférico ámbar con partículas animadas sutiles
- **Texto:** "Sube una foto de tu habitación" en Blanco Lunar, "o arrastra aquí" en Plata Nebulosa

### Pricing Card

- **Diseño:** Tarjeta destacada con borde gradiente ámbar-violeta animado
- **Precio:** "2,50€" en Ámbar Dorado, extra-bold, 3-4rem centrado
- **Comparación:** Texto tachado "3,50€ (precio de un perrito 🌭)" en Plata Nebulosa
- **Badge:** "¡1€ MENOS!" en pill-shape con fondo Ámbar, texto oscuro

### Inputs & Forms

- **Stroke Style:** Borde refinado 1.5px en Gris Estelar
- **Background:** Obsidiana Cálida (#1C2333) con transición a Carbón Suave en focus
- **Corner Style:** Matching con botones (12px/0.75rem) para consistencia visual
- **Focus State:** Borde transiciona a Ámbar Dorado con glow exterior sutil
- **Padding:** 1rem vertical, 1.5rem horizontal para targets táctiles cómodos
- **Placeholder Text:** Gris Estelar con estilo elegante e imperceptible

## 5. Layout Principles

### Grid & Structure

- **Max Content Width:** 1280px para balance óptimo en pantallas grandes
- **Grid System:** Grid responsive de 12 columnas con gutters fluidos (16px mobile, 24px desktop)
- **Gallery Grid:** 3 columnas en desktop, 2 en tablet, 1 en mobile para renders
- **Breakpoints:**
  - Mobile: <768px
  - Tablet: 768-1024px
  - Desktop: 1024-1280px
  - Large Desktop: >1280px

### Whitespace Strategy (Critical to the Design)

- **Base Unit:** 8px para micro-spacing, 16px para spacing de componentes
- **Vertical Rhythm:** 2rem (32px) consistente entre elementos relacionados
- **Section Margins:** 6-10rem (96-160px) generosos entre secciones para impacto dramático
- **Edge Padding:** 1.5rem mobile, 4rem desktop para enmarcado elegante
- **Hero Sections:** Padding extra-generoso (10-14rem) arriba y abajo para presentación cinematográfica

### Alignment & Visual Balance

- **Text Alignment:** Centrado para hero headlines y CTAs, izquierda para contenido de lectura
- **Image to Content Ratio:** 65-35 split, prioridad absoluta a las imágenes de renders
- **Visual Flow:** Patrón Z clásico: Logo → Nav → Hero Image → Precio → CTA
- **Focal Points:** Imágenes de renders y precio "2,50€" como puntos de atracción principales

### Responsive Behavior & Touch

- **Mobile-First:** Experiencia core diseñada para móvil primero
- **Progressive Enhancement:** Más columnas, detalles e imágenes en breakpoints mayores
- **Touch Targets:** Mínimo 48x48px para todos los elementos interactivos
- **Image Optimization:** Lazy loading, WebP, responsive srcset para rendimiento
- **Animaciones:** Reducidas en preferencia de movimiento reducido (prefers-reduced-motion)

## 6. Design System Notes for Stitch Generation

Cuando crees nuevas pantallas para este proyecto en Stitch, referencia estas instrucciones específicas:

### Language to Use

- **Atmosphere:** "Oasis tecnológico cálido y aspiracional con estética nocturna premium"
- **Button Shapes:** "Esquinas generosamente redondeadas" (no "rounded-lg" o "12px")
- **Shadows:** "Sombras difusas con glow ámbar cálido en hover" (no "shadow-lg")
- **Spacing:** "Respiración dramática" y "espacio cinematográfico entre secciones"

### Color References

Siempre usa los nombres descriptivos con hex codes:

- Primary CTA: "Ámbar Dorado Brillante (#F0A500)"
- Backgrounds: "Noche Profunda (#0D1117)" o "Carbón Suave (#161B22)"
- Text: "Blanco Lunar (#E6EDF3)" o "Plata Nebulosa (#8B949E)"
- AI Accent: "Violeta Eléctrico Profundo (#7C3AED)"

### Component Prompts

- "Create a render showcase card with suavemente redondeadas corners, full-bleed 16:9 render preview image, and warm amber glow shadow on hover over a dark Noche Profunda background"
- "Design a hero section with dramatic cinematic spacing, displaying '2,50€' price prominently in Ámbar Dorado with a strikethrough comparison to hot dog price"
- "Add an upload zone with dashed border that illuminates to Ámbar Dorado on drag, with camera icon pulse animation"
- "Create a before/after slider with Ámbar Dorado divider line and glassmorphism labels"

### Incremental Iteration

When refining existing screens:

1. Focus on ONE component at a time
2. Be specific about what to change
3. Reference this design system language consistently
4. Maintain the dark premium atmosphere throughout
