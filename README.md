# Tandil Tech Week — réplica estática

Réplica local de [tandiltechweek.com](https://tandiltechweek.com) hecha a partir
del HTML servido por el sitio original. **HTML + CSS + JS puro: sin dependencias,
sin paso de build, sin `node_modules`.**

---

## Arrancar en local

El sitio no necesita Node.js para funcionar. Cualquiera de estas opciones sirve:

```bash
# Opción A — Python (no requiere instalar nada)
python3 serve.py

# Opción B — Node.js >= 18
npm start          # o: node server.js
```

Luego abrí <http://localhost:4173>.

| Comando | Qué hace |
| --- | --- |
| `python3 serve.py` | Servidor local (Python, cero dependencias) |
| `npm start` / `node server.js` | Servidor local (Node, cero dependencias) |
| `npm run build` | Regenera el HTML a partir de `tools/src/` |
| `npm run check` | Valida enlaces internos y referencias a assets |

Ambos servidores incluyen URLs limpias (`/hacking-day` → `hacking-day/index.html`),
MIME types correctos, compresión gzip, 404 propio y protección contra path traversal.

---

## Estructura

```
.
├── index.html                  # Home
├── hacking-day/index.html      # Hacking Day
├── startup-day/index.html      # Startup Day
├── 404.html
├── robots.txt
├── sitemap.xml
├── server.js                   # servidor estático (Node)
├── serve.py                    # servidor estático (Python)
├── package.json
├── assets/
│   ├── css/style.css           # sistema de diseño completo
│   ├── js/main.js              # contador + revelado al scroll
│   ├── fonts/                  # Switzer Variable (woff2)
│   ├── img/                    # favicons, social card, logo Payoneer
│   └── logos/                  # SVGs originales de los sponsors
└── tools/
    ├── build.py                # generador del HTML final
    ├── check.py                # validador de enlaces/assets
    └── src/                    # HTML servido por el sitio original
```

---

## Sistema de diseño

Todo vive en `assets/css/style.css`, organizado por tokens en `:root`.
Cambiar un color o una escala tipográfica se hace en un solo lugar.

**Paleta**

| Token | Valor | Uso |
| --- | --- | --- |
| `--paper` | `#f4f3ef` | Fondo principal (hueso) |
| `--ink` | `#292929` | Texto y bordes |
| `--ink-muted` | `#5c5c5c` | Texto secundario |
| `--blue` | `#1000ff` | Color de marca |
| `--green` | `#28ad1d` | Acento verde |
| `--green-ink` | `#17700f` | Verde oscuro (sobre verde) |
| `--soft` | `#e6e5e0` | Fondo de secciones alternas |
| `--line` | `#d5d3cc` | Bordes y separadores |

**Tipografía**: Switzer Variable, con fallback métrico sobre Arial para evitar el
salto de layout (CLS) durante la carga.

**Escala fluida**: `--text-s` → `--text-h1`, todas con `clamp()`. El resto de las
medidas (gutter, espacios de sección, alto del header) también son tokens.

**Retícula**: `.poster-hero` usa un grid de 24 columnas con `--grid-edge`, que
permite que el panel azul llegue al borde exacto de la pantalla.

---

## Cómo mejorarla

### Cambiar un color, una fuente o el espaciado
Editá los tokens en `:root` dentro de `assets/css/style.css`. No hay que tocar
ninguna otra parte.

### Cambiar la fecha del evento
1. `index.html` → `<time class="date-number" datetime="...">14&15</time>`
2. `assets/js/main.js` no guarda fechas: se leen de `data-countdown-to` en el HTML.
3. JSON-LD en el `<head>` de cada página (`startDate`, `endDate`, `offers.validFrom`).
4. `sitemap.xml` y `robots.txt`.

### Cambiar un logo de sponsor
Los logos están **inline en el HTML** (para que el hover pueda cambiarles el color
con `currentColor`). Buscá el bloque `<h3 class="card__logo">` en la sección
`#organizan` o `#acompanan` y reemplazá el `<svg>`.

Los originales quedan en `assets/logos/*.svg` como referencia.

Para reemplazar varios logos de forma masiva: editá los `.svg` en `assets/logos/`
y regenerá con `python3 tools/build.py` (ver más abajo).

### Reagendar o cambiar contenido
Si editás los `.html` a mano, ya está: son archivos estáticos, se sirven tal cual.
Si en cambio editás `tools/src/*.src.html` (el HTML crudo del sitio original),
corré `python3 tools/build.py` para regenerar.

---

## Qué se mejoró respecto del original

La réplica es visualmente idéntica, pero la base técnica es más simple y robusta:

| Antes (original) | Ahora |
| --- | --- |
| Next.js App Router + React | HTML estático, sin hidratación |
| Tailwind v4 compilado en build | CSS propio con tokens, sin build |
| GSAP + ScrollTrigger (~70 kB) | IntersectionObserver nativo (~4 kB) |
| Hidratación de React para el contador | JS progresivo, funciona sin JS |
| Sin skip link | Skip link accesible con teclado |
| URLs de `/_next/static/...` | Assets propios con rutas estables |
| Sin `robots.txt` ni `sitemap.xml` | Ambos incluidos |
| Sin página 404 | 404 con el mismo sistema de diseño |

### Accesibilidad
- Skip link, `<main>` enfocable, `:focus-visible` con outline de 2 px en toda la UI.
- El contador tiene texto para lectores de pantalla (`.sr-only`) y la parte
  decorativa marcada con `aria-hidden`.
- `prefers-reduced-motion` desactiva la marquesina, el revelado al scroll y las
  transiciones.
- SVG decorativos con `aria-hidden`, logos con `role="img"` + `aria-label`.

### Rendimiento
- Fuente con `preload` + `font-display: swap` + fallback métrico.
- Cero JavaScript bloqueante; `main.js` se carga con `defer`.
- Sin dependencias: 1 CSS + 1 JS + 1 fuente.
- Compresión gzip/brotli en el servidor.

---

## Limitaciones conocidas

- **Sin navegación móvil**: el menú se oculta por debajo de 900 px, igual que el
  original. Es la primera mejora pendiente si querés sumarla.
- **Rutas absolutas**: los enlaces internos usan `/hacking-day`. Si servís el
  sitio desde un subdirectorio, hay que ajustarlos a relativos.
- **Embeds de Luma**: los iframes apuntan a `luma.com` y requieren conexión.
- **Hero en `100svh`**: usa unidades `svh`, soportadas en todos los navegadores
  modernos.
- **`.line-week`**: existe como hook semántico en el HTML pero no tiene regla CSS,
  igual que en el original.

---

## Verificar

```bash
python3 tools/check.py   # enlaces internos + referencias a assets
```
