# Theme / Tailwind Config ( Design Tokens

##embebido en cada HTML)

```javascript
tailwind.config = {
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "primary": "#f0a400",
                "background-light": "#f8f7f5",
                "background-dark": "#0D1117",
                "charcoal": "#161B22",
                "nebula": "#C9D1D9"
            },
            fontFamily: { "display": ["Inter", "sans-serif"] },
            borderRadius: { "DEFAULT": "0.5rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px" },
        },
    },
}
```

## CSS Variables y Estilos Globales

```css
.glass-nav { 
    background: rgba(13,17,23,0.7); 
    backdrop-filter: blur(12px); 
    -webkit-backdrop-filter: blur(12px); 
}

.amber-glow { 
    box-shadow: 0 0 20px rgba(240,164,0,0.15); 
}

.gradient-border { 
    position: relative; 
    background: #161B22; 
    border-radius: 1.5rem; 
}

.gradient-border::before {
    content:""; 
    position:absolute; 
    inset:-2px; 
    z-index:-1;
    background:linear-gradient(45deg,#f0a400,#7c3aed); 
    border-radius:1.6rem; 
}
```

## Fuentes
- **Inter** (Google Fonts) - Font principal
- **Material Symbols Outlined** - Iconos

## Colores
- Primary: `#f0a400` (Amber/Gold)
- Background Dark: `#0D1117` (GitHub dark)
- Charcoal: `#161B22`
- Nebula: `#C9D1D9`

## Modo
- Dark mode por defecto con clase `dark` en el HTML
