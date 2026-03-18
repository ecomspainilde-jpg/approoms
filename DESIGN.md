# Design System: RenderRoom AI (Solar Light)
**Project ID:** 10149300038889827122

## 1. Visual Theme & Atmosphere

The RenderRoom "Solar Light" theme embodies an **aspirational, high-clarity, and modern sanctuary** that reflects the precision and speed of AI-powered interior design. The interface is **bright, spacious, and energetic**, prioritizing visual realism and light-filled environments. The design philosophy is photography-first, treating AI-generated renders as the primary focal point of the user experience.

The overall mood is **professional yet vibrant**, creating a sense of immediate transformation and possibilities. The interface feels **premium through its restraint**, using subtle glassmorphism and balanced proportions to guide the user without visual clutter. The atmosphere evokes the clarity of a sunlit studio, where architectural precision meets creative inspiration.

**Key Characteristics:**
- **High-Key Luminosity**: Extensive use of pure white backgrounds and solar-toned accents.
- **Organic Precision**: Large border radii (rounded-3xl) that communicate friendliness and modern comfort.
- **Glassmorphism**: Elegant, translucid navigation and card elements that add depth and sophistication.
- **Aspirational Tone**: High-contrast, bold typography that feels authoritative and modern.
- **Solar Glow**: Strategic use of warm, diffuse shadows that highlight key interaction points.

## 2. Color Palette & Roles

### Primary Foundation
- **Solar White** (#FFFFFF) – Primary background color. Creates a sense of unlimited space and clean architectural clarity.
- **Alice Blue Light** (#F8FAFC) – Secondary surface color used for section backgrounds and card foundations. Provides subtle visual separation while maintaining the airy aesthetic.
- **Carbon Gray** (#1A1A1A) – Primary secondary color for dark UI elements, navigation headers, and semantic grounding.

### Accent & Interactive
- **Amber-Gold Brillante** (#FFB800) – The primary brand accent. Used for primary CTAs, active states, and "Glow" effects. This color evokes sunlight and energy.
- **Flame Orange** (#FF7A00) – Supporting accent color for gradients and secondary visual highlights, adding warmth and depth to the primary amber.

### Typography & Text Hierarchy
- **Deep Slate** (#111827) – Primary text color for headlines and important labels. Provides maximum readability and a premium, grounded feel.
- **Steel Blue Gray** (#475569) – Secondary text for body copy and supporting descriptions. Softer contrast for comfortable reading.
- **Mist Border** (#F1F5F9) – Tertiary color for subtle structural elements, thin borders, and divider lines.

### Functional States (Stitch Alignment)
- **Verified Green** (#22C55E) – Success states, credit confirmations, and finalized renders.
- **Warning Sunset** (#F59E0B) – Alert states, low credit warnings.
- **Error Ruby** (#EF4444) – Critical errors or failed operations.

## 3. Typography Rules

### Primary Font Stack
- **Headline Font:** Outfit / Plus Jakarta Sans  
- **UI & Display:** Plus Jakarta Sans  
- **Body Context:** Inter / Sans-serif

### Hierarchy & Weights
- **Hero Display (H1):** Black (900) or ExtraBold (800) weight, 3.5rem to 4.5rem size on desktop. Minimal letter-spacing for maximum impact.
- **Section Headers (H2):** Black (900) weight, 2rem to 2.5rem size. Defines content blocks with authority.
- **Subsection Titles (H3):** Bold (700) weight, 1.25rem to 1.5rem size. Card headers and feature labels.
- **Body Copy:** Regular (400) or Medium (500) weight, line-height 1.6, 1rem size. Prioritizes clarity and readability.
- **Micro-Copy:** Bold (700) or ExtraBold (800) uppercase, tracked (0.1em), 0.75rem. Used for badges and status labels.

### Spacing Principles
- Headlines use tight tracking for a "cinematic" and premium look.
- Body text uses generous line-height to maintain the "airy" feel of the Solar theme.
- Significant vertical spacing (6rem to 8rem) between major landing sections.

## 4. Component Stylings

### Buttons
- **Shape:** Large rounded corners (rounded-xl/2xl, approx. 1rem to 1.5rem radius).
- **Primary Action:** Amber-Gold gradient (#FFB800 to #FF7A00) with Carbon Gray or White text. Includes `solar-glow` shadow on hover.
- **Secondary Action:** Ghost or Outlined style with precise borders and subtle text contrast.
- **Hover Transitions:** Smooth 300ms ease-in-out with slight scaling (1.05x).

### Cards & Layout Modules
- **Corner Style:** Extra-large radii (`rounded-3xl` / 2rem).
- **Background:** Solid #FFFFFF with whisper-soft borders in #F1F5F9.
- **Inner Padding:** Generous 2.5rem to 3rem creating "gallery-like" breathing room.
- **Shadow strategy:** `solar-glow` (warm, amber-tinted diffuse shadow) to create depth without generic black offsets.

### Navigation & Header
- **Style:** Sticky top navigation with glassmorphism (`backdrop-blur-xl`).
- **Surface:** `bg-white/90` with a subtle bottom border in #F1F5F9.
- **Interaction:** Nav links transition to Amber-Gold (#FFB800) on hover.

### Design Specifics: "Solar Glow"
Any core UI element (Hero image, pricing card, or main CTA) should use a diffuse amber shadow: 
`box-shadow: 0 10px 40px rgba(245, 158, 11, 0.12);`

## 5. Layout Principles

### Grid & Structure
- **Max Width:** 1280px (7xl) – balanced for photographic showcases.
- **Vertical Rhythm:** Generous spacing units (8px base). Sections separated by 24 (96px) or 32 (128px) units.
- **Split Hero:** 50/50 split between high-impact typography and cinematic image/slider showcases.

### Whitespace Strategy
- **Architectural Breathing Room:** Intentionally large gaps between sections to prevent "feature crowding".
- **Photography Focus:** UI elements never overlap the focal points of the render showcases.

## 6. Design System Notes for Stitch Generation
When using Stitch to generate new screens for the RenderRoom project, follow these specific instructions:

### Tone & Style Prompting
- "Use the Solar Light theme: white backgrounds, high-energy amber accents, and generous architectural whitespace."
- "Apply extra-large corner rounding (rounded-3xl) to all main content cards."
- "Use Outfit Black (900) for hero headlines to create a cinematic impact."

### Component References
- **Cards**: "Glassmorphic or solid white cards with rounded-3xl corners and subtle solar-glow shadows."
- **Buttons**: "High-contrast Amber-Gold buttons with rounded-xl corners and smooth hover transitions."
- **Transitions**: "Use subtle fade-ins and smooth ease-out-back animations for a premium feel."
