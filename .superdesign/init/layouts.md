# Layouts

Este proyecto es HTML estático. No hay componentes de layout separados - cada página HTML incluye su propia navegación y estructura.

## Estructuras comunes encontradas en las páginas

### Navegación Principal (Glass Nav)
```html
<nav class="glass-nav fixed top-0 inset-x-0 z-50 border-b border-white/5">
  <!-- Logo + Links + CTA -->
</nav>
```

### Footer
```html
<footer class="bg-charcoal border-t border-white/5 py-12">
  <!-- Links, redes sociales, legal -->
</footer>
```

### Auth Modal
```html
<div id="auth-modal" class="hidden fixed inset-0 z-[100]">
  <!-- Login/Register forms -->
</div>
```

Todos los archivos de páginas incluyen su propia navegación y footer embebidos.
