# Design System - RenderRoom

## Product Context
- **Product**: RenderRoom AI - Interior design rendering service
- **Target Users**: Home owners wanting to visualize room redesigns
- **Key Value**: AI-powered room rendering for 2.50€ per render

## Brand & Styling

### Colors
- **Primary**: `#f0a400` (Amber/Gold)
- **Primary Hover**: `#d4940a`
- **Background Dark**: `#0D1117` (GitHub dark)
- **Background Light**: `#f8f7f5`
- **Surface/Charcoal**: `#161B22`
- **Text Primary**: `#C9D1D9` (Nebula silver)
- **Text Muted**: `#8b949e`
- **Border**: `rgba(255,255,255,0.1)`

### Typography
- **Font Family**: Inter (Google Fonts)
- **Font Weights**: 300, 400, 500, 600, 700, 800, 900
- **Headings**: Bold, tracking-tight
- **Body**: Regular, 14-16px
- **Labels**: Uppercase, 12px, font-semibold

### Components
- **Buttons**: 
  - Primary: bg-primary text-background-dark font-black, rounded-xl, hover:scale-105
  - Secondary: border-primary/40 text-primary, hover:bg-primary/10
- **Cards**: bg-surface-dark rounded-xl border border-white/5
- **Inputs**: bg-background-dark border-white/10 rounded-lg, focus:ring-primary
- **Nav**: Glass nav with backdrop blur, fixed top

### Layout
- Max width: max-w-7xl (1280px)
- Spacing: 6 (1.5rem) base
- Border radius: lg (1rem), xl (1.5rem), full (9999px)
- Shadows: shadow-primary/20 for amber glow effects

### Icons
- Material Symbols Outlined (Google Fonts)

## Dark Mode
- Default enabled with class `dark` on HTML element
