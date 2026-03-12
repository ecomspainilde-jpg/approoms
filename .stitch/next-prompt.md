---
page: quick_purchase_modal
---
Modal de compra rápida de créditos para RenderRoom. Se muestra superpuesto cuando el usuario quiere comprar más créditos sin salir de su pantalla actual.

**DESIGN SYSTEM (REQUIRED):**
Tema oscuro y aspiracional. Fondo overlay semi-transparente oscuro sobre la página. El modal en Carbón Suave (#161B22) con borde glassmorphism sutil y glow ámbar exterior. Acento Ámbar Dorado Brillante (#F0A500). Tipografía Inter, texto Blanco Lunar (#E6EDF3) y secundario Plata Nebulosa (#8B949E). Bordes 16px redondeados extragrandes en el modal.

**Page Structure:**
Modal centrado en overlay oscuro translúcido:
1. Header del modal: título "Añadir créditos" con ícono ámbar de moneda, botón X de cierre en esquina.
2. Selector de paquetes en 3 mini-tarjetas horizontales clickables (radio-button visual):
   - "1 Render — 2,50€" con radio-input
   - "5 Renders — 10,00€" (pre-seleccionado, borde ámbar brillante) badge "El más popular"
   - "20 Renders — 30,00€" badge "Para profesionales"
3. Resumen: "Total a pagar: 10,00€" en grande con ámbar + "5 créditos se añadirán a tu cuenta"
4. Sección de métodos de pago: fila de pequeños logos: Visa, Mastercard, Google Pay, Apple Pay, PayPal, Revolut
5. Botón CTA gigante de ancho completo: gradiente ámbar "Pagar con Stripe →"
6. Texto pequeño inferior: "🔒 Pago seguro. Puedes cancelar en cualquier momento."
