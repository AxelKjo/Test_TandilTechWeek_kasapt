#!/usr/bin/env python3
"""
Servidor estático sin dependencias (solo Python 3.9+).
-----------------------------------------------------
Alternativa a `server.js` para entornos sin Node.js instalado.

Uso:  python3 serve.py [--port 4173] [--host 0.0.0.0]

Incluye URLs limpias, MIME types correctos, compresión gzip y 404 propio.
"""

import argparse
import gzip
import os
import sys
from http import server
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
PORT = 4173
HOST = "localhost"

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".txt": "text/plain; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
}

CACHEABLE = (".css", ".js", ".woff2", ".png", ".svg", ".ico", ".webp", ".woff", ".ttf")


def resolve_file(url_path: str):
    """Devuelve la ruta real a servir, o None si no existe."""
    path = unquote(urlsplit(url_path).path)
    candidate = (ROOT / path.lstrip("/")).resolve()

    # Bloquea path traversal fuera del directorio servido.
    if candidate != ROOT and ROOT not in candidate.parents:
        return None

    if candidate.is_dir():
        candidate = candidate / "index.html"

    if candidate.is_file():
        return candidate

    # URL limpia sin extensión: /hacking-day -> /hacking-day/index.html
    if candidate.suffix == "":
        nested = candidate / "index.html"
        if nested.is_file():
            return nested
    return None


class Handler(server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # logging más limpio
        sys.stderr.write("  %s\n" % (fmt % args))

    def _headers(self, path: Path):
        suffix = path.suffix.lower()
        headers = {
            "Content-Type": MIME.get(suffix, "application/octet-stream"),
            "Cache-Control": (
                "public, max-age=86400" if suffix in CACHEABLE else "no-cache"
            ),
        }
        if "gzip" in self.headers.get("Accept-Encoding", ""):
            headers["Content-Encoding"] = "gzip"
        return headers

    def _serve(self, head_only: bool):
        path = resolve_file(self.path)

        if path is None:
            path = resolve_file("/404.html")
            status = 404
            if path is None:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                if not head_only:
                    self.wfile.write(b"404 Not Found")
                return
        else:
            status = 200

        body = path.read_bytes()
        headers = self._headers(path)

        if "Content-Encoding" in headers:
            body = gzip.compress(body, compresslevel=6)

        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def do_GET(self):
        self._serve(head_only=False)

    def do_HEAD(self):
        self._serve(head_only=True)


def main():
    global HOST, PORT

    parser = argparse.ArgumentParser(description="Servidor estático sin dependencias")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--host", default=HOST)
    args = parser.parse_args()
    PORT, HOST = args.port, args.host

    with server.ThreadingHTTPServer((HOST, PORT), Handler) as httpd:
        print(f"\n  Tandil Tech Week — réplica local")
        print(f"  → http://{HOST}:{PORT}\n")
        print("  Ctrl+C para detener\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Servidor detenido.\n")


if __name__ == "__main__":
    main()
