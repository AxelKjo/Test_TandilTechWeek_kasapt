#!/usr/bin/env python3
"""
Generador de la réplica estática de tandiltechweek.com
-----------------------------------------------------
Parte del HTML servido por el sitio original y produce archivos estáticos
limpios:

  * sustituye las utilities de Tailwind por clases semánticas propias,
  * mueve el JSON-LD al <head>,
  * elimina los artefactos del pipeline de React/Next.js,
  * añade mejoras de accesibilidad (skip link, <main> enfocable),
  * externaliza la fecha del contador a un data-attribute.

Uso:  python3 tools/build.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "src"
OUT = ROOT

SITE = "https://tandiltechweek.com"
COUNTDOWN_TARGET = "2026-09-17T19:00:00-03:00"
OPEN_MESSAGE = "Las inscripciones ya están abiertas."

# --------------------------------------------------------------------------
# Mapeo de utilities de Tailwind -> clases propias
# --------------------------------------------------------------------------

DROP = {
    "group",
    "transition-shadow",
    "hover:shadow-[5px_5px_0_0_var(--blue)]",
    "transition-colors",
    "group-hover:text-[var(--blue)]",
}

RENAME = {
    "text-[var(--blue)]": "c-blue",
    "text-[var(--green)]": "c-green",
    "text-[var(--green-ink)]": "c-green-ink",
    "text-[var(--ink)]": "c-ink",
    "text-[var(--ink-muted)]": "c-muted",
    "text-[var(--paper)]": "c-paper",
    "bg-[var(--blue)]": "bg-blue",
    "bg-[var(--green)]": "bg-green",
    "bg-[var(--paper)]": "bg-paper",
    "font-normal": "fw-normal",
    "font-medium": "fw-medium",
    "mt-3": "mt-3",
    "uppercase": "tracked",
    "tracking-[0.1em]": "tracked",
}


def transform_class_attribute(value: str) -> str:
    tokens = value.split()

    # Caso 1: punto verde del tag "Coming Soon" -> .dot
    if {"w-2", "h-2", "rounded-full", "bg-[var(--green)]"} <= set(tokens):
        return "dot"

    # Caso 2: enlace inline tipo "Abrir en Luma" -> .link-inline
    if "inline-flex" in tokens and "min-h-6" in tokens:
        return "link-inline"

    out = [RENAME.get(t, t) for t in tokens if t not in DROP]

    # Deduplica preservando el orden
    seen, result = set(), []
    for token in out:
        if token not in seen:
            seen.add(token)
            result.append(token)
    return " ".join(result)


def transform_classes(html: str) -> str:
    return re.sub(
        r'class="([^"]*)"',
        lambda m: 'class="{}"'.format(transform_class_attribute(m.group(1))),
        html,
    )


# --------------------------------------------------------------------------
# Limpieza de artefactos de React / Next.js
# --------------------------------------------------------------------------

def clean_markup(html: str) -> str:
    html = re.sub(r"<!--\$-->|<!--/\$-->|<!--\$!-->", "", html)
    html = html.replace("<!-- -->", "")
    html = re.sub(r"<div hidden=\"\">\s*</div>", "", html)
    html = re.sub(r"<template[^>]*>.*?</template>", "", html, flags=re.S)
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S)
    html = re.sub(r"<script\b[^>]*></script>", "", html)
    return rewrite_asset_urls(html)


# Rutas de assets del sitio original -> rutas de la réplica.
ASSET_REWRITES = {
    "/logos/": "/assets/img/",
    "/social-card.png": "/assets/img/social-card.png",
    "/favicon.ico": "/assets/img/favicon.ico",
    "/icon.svg": "/assets/img/icon.svg",
    "/apple-icon.png": "/assets/img/apple-icon.png",
}


def rewrite_asset_urls(html: str) -> str:
    for original, replacement in ASSET_REWRITES.items():
        html = html.replace(f'"{original}', f'"{replacement}')
        html = html.replace(f"'{original}", f"'{replacement}")
    return html


def extract_json_ld(html: str):
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    )
    cleaned = re.sub(
        r'<script type="application/ld\+json">.*?</script>', "", html, flags=re.S
    )
    return cleaned, blocks


def extract_body(html: str) -> str:
    match = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    body = match.group(1)
    return body.split('<script>self.__next_f.push')[0]


# --------------------------------------------------------------------------
# Head
# --------------------------------------------------------------------------

SOCIAL_ALT = (
    "Póster de Tandil Tech Week 2026: “14&15 OCT.” en tipografía "
    "sobredimensionada sobre fondo hueso, junto a un panel azul eléctrico con una "
    "forma orgánica que contiene el logotipo “2026 Tandil Tech Week”."
)

FAVICONS = """<link rel="icon" href="/assets/img/favicon.ico" sizes="48x48" type="image/x-icon">
<link rel="icon" href="/assets/img/icon.svg" sizes="any" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/apple-icon.png" sizes="180x180">"""

PRELOAD_FONT = (
    '<link rel="preload" href="/assets/fonts/Switzer-Variable.woff2" '
    'as="font" type="font/woff2" crossorigin>'
)


def build_head(page: dict) -> str:
    og_image = f"{SITE}/assets/img/social-card.png"
    ld = "\n".join(
        f'<script type="application/ld+json">{b}</script>' for b in page["json_ld"]
    )
    return f"""<head>
<meta charSet="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page['title']}</title>
<meta name="description" content="{page['description']}">
<link rel="canonical" href="{page['canonical']}">
<meta name="theme-color" content="#1000ff">
<meta name="color-scheme" content="light">
<meta property="og:title" content="{page['title']}">
<meta property="og:description" content="{page['description']}">
<meta property="og:url" content="{page['canonical']}">
<meta property="og:site_name" content="Tandil Tech Week">
<meta property="og:locale" content="es_AR">
<meta property="og:image" content="{og_image}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="2400">
<meta property="og:image:height" content="1260">
<meta property="og:image:alt" content="{SOCIAL_ALT}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@tandiltechweek">
<meta name="twitter:creator" content="@tandiltechweek">
<meta name="twitter:title" content="{page['title']}">
<meta name="twitter:description" content="{page['description']}">
<meta name="twitter:image" content="{og_image}">
<meta name="twitter:image:alt" content="{SOCIAL_ALT}">
{FAVICONS}
{PRELOAD_FONT}
<link rel="stylesheet" href="/assets/css/style.css">
{ld}</head>"""


# --------------------------------------------------------------------------
# Transformaciones sobre el body
# --------------------------------------------------------------------------

def insert_into_div(html: str, class_attr: str, insert: str) -> str:
    """Inserta `insert` como último hijo del <div class="class_attr">.

    Busca el cierre correcto contando la profundidad de anidamiento, para no
    confundirlo con el de un div interno.
    """
    match = re.search(
        r'<div class="' + re.escape(class_attr) + r'"[^>]*>', html
    )
    if not match:
        raise SystemExit(f'No se encontró <div class="{class_attr}">')

    depth, pos = 1, match.end()
    while depth > 0:
        next_open = html.find("<div", pos)
        next_close = html.find("</div>", pos)
        if next_close == -1:
            raise SystemExit(f'HTML desbalanceado dentro de .{class_attr}')
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            pos = next_close + 6

    return html[: next_close] + insert + html[next_close :]


def externalize_countdown(body: str) -> str:
    """La fecha pasa a un data-attribute y se añade el estado 'abierto'."""
    body = body.replace(
        '<div class="countdown">',
        f'<div class="countdown" data-countdown-to="{COUNTDOWN_TARGET}">',
    )
    return insert_into_div(
        body, "countdown", f'<p class="countdown__open">{OPEN_MESSAGE}</p>'
    )


def build_page(page: dict, source: str) -> str:
    source, json_ld = extract_json_ld(source)
    body = clean_markup(extract_body(source))
    body = transform_classes(body)
    body = externalize_countdown(body)

    # Accesibilidad: destino para el skip link y <main> enfocable.
    body = body.replace("<main>", '<main id="main" tabindex="-1">', 1)
    body = '<a class="skip-link" href="#main">Saltar al contenido</a>' + body

    head = build_head({**page, "json_ld": json_ld})

    return (
        "<!DOCTYPE html>\n"
        '<html lang="es-AR">\n'
        f"{head}\n"
        "<body>\n"
        f"{body}\n"
        '<script src="/assets/js/main.js" defer></script>\n'
        "</body>\n</html>\n"
    )


# --------------------------------------------------------------------------
# Páginas
# --------------------------------------------------------------------------

PAGES = [
    ("index.src.html", OUT / "index.html", {
        "title": "Tandil Tech Week · 14 &amp; 15 octubre 2026",
        "description": (
            "14 y 15 de octubre de 2026 en Tandil. Dos días para conectar "
            "el ecosistema startup y conocer a los que hacen."
        ),
        "canonical": f"{SITE}/",
    }),
    ("hacking-day.src.html", OUT / "hacking-day" / "index.html", {
        "title": "Hacking Day · Tandil Tech Week 2026",
        "description": (
            "Jornada de hacking en equipos. Juntá a tus amigos y vení a "
            "divertirte aprendiendo de ciberseguridad."
        ),
        "canonical": f"{SITE}/hacking-day",
    }),
    ("startup-day.src.html", OUT / "startup-day" / "index.html", {
        "title": "Startup Day · Tandil Tech Week 2026",
        "description": (
            "Vení a conocer a los que hacen. Charlas dinámicas y networking "
            "entre fundadores, venture capital y estudiantes."
        ),
        "canonical": f"{SITE}/startup-day",
    }),
]


def main() -> int:
    for filename, destination, meta in PAGES:
        source = (SRC / filename).read_text(encoding="utf-8")
        html = build_page(meta, source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(html, encoding="utf-8")
        print(f"  OK  {destination.relative_to(OUT)}  ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
