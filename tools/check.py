#!/usr/bin/env python3
"""
Validador de la réplica estática
--------------------------------
Comprueba que no queden enlaces internos ni referencias a assets rotras,
y que no hayan quedado utilities de Tailwind sin mapear.

Uso:  python3 tools/check.py
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("*/*.html"))

TAILWIND_LEFTOVERS = re.compile(
    r"(?:text|bg|hover|group-hover|focus-visible|min-h)-\[|"
    r"\b(?:group|transition-shadow|transition-colors|rounded-full|font-normal|font-medium|"
    r"uppercase|tracking-\[|inline-flex|min-h-6|items-center|w-2|h-2)\b"
)

ASSET_ATTRS = ("href", "src")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ASSET_ATTRS and value:
                self.refs.append(value)


def main() -> int:
    errors = []
    checked = 0

    for page in PAGES:
        if "tools" in page.parts:
            continue

        html = page.read_text(encoding="utf-8")
        rel = page.relative_to(ROOT)
        checked += 1

        # 1. Sin utilities de Tailwind huérfanas
        for match in re.finditer(r'class="([^"]*)"', html):
            if TAILWIND_LEFTOVERS.search(match.group(1)):
                errors.append(f"{rel}: utility sin mapear → {match.group(1)}")

        # 2. Referencias locales que existen
        parser = LinkParser()
        parser.feed(html)

        for ref in parser.refs:
            parsed = re.match(r"^/([^#?]*)", ref)
            if not parsed:
                continue  # externa, ancla o protocolo
            path = parsed.group(0).lstrip("/")
            if not path:
                continue

            target = (ROOT / path).resolve()
            if target.is_dir():
                target = target / "index.html"

            if not target.is_file():
                errors.append(f"{rel}: recurso inexistente → {ref}")

    print(f"\n  Páginas revisadas: {checked}")
    if errors:
        print(f"  Problemas encontrados: {len(errors)}\n")
        for error in errors:
            print(f"    · {error}")
        print()
        return 1

    print("  Todo en orden: enlaces y assets OK, sin utilities huérfanas.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
