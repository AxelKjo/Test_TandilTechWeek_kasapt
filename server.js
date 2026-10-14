/**
 * Servidor estático sin dependencias (solo Node.js >= 18).
 * --------------------------------------------------------------------------
 * Uso:  node server.js [--port 4173] [--host]
 *
 * Qué hace bien para una réplica local:
 *   · URLs limpias  ->  /hacking-day sirve /hacking-day/index.html
 *   · MIME types correctos (woff2, svg, ico, webmanifest...)
 *   · compresión gzip/brotli cuando el navegador la acepta
 *   · cabeceras de cache diferenciadas para HTML y assets
 *   · página 404 propia
 *   · sin node_modules
 */

import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { extname, join, normalize, resolve, sep, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createGzip, createBrotli } from "node:zlib";
import { pipeline } from "node:stream";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)));
const HOST = process.argv.includes("--host") ? "0.0.0.0" : "localhost";
const portFlag = process.argv.indexOf("--port");
const PORT = Number(portFlag > -1 ? process.argv[portFlag + 1] : 4173);

const MIME = {
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
  ".webmanifest": "application/manifest+json",
};

/** Resuelve una URL limpia a un archivo real dentro de ROOT, o null. */
async function resolveFile(urlPath) {
  const clean = decodeURIComponent(urlPath.split("?")[0].split("#")[0]);
  let filePath = normalize(join(ROOT, clean));

  // Previene path traversal fuera del directorio servido.
  if (filePath !== ROOT && !filePath.startsWith(ROOT + sep)) return null;

  try {
    let info = await stat(filePath);
    if (info.isDirectory()) {
      filePath = join(filePath, "index.html");
      info = await stat(filePath);
    }
    if (!info.isFile()) return null;
    return { filePath, size: info.size, mtime: info.mtime };
  } catch {
    // Sin extensión: probamos el index.html del directorio (URL limpia).
    if (extname(filePath) === "") {
      try {
        const candidate = join(filePath, "index.html");
        const info = await stat(candidate);
        if (info.isFile()) {
          return { filePath: candidate, size: info.size, mtime: info.mtime };
        }
      } catch {
        /* sigue al 404 */
      }
    }
    return null;
  }
}

/**
 * Decide si conviene comprimir y con qué algoritmo.
 * Devuelve las cabeceras finales y el stream transformador (o null).
 */
function compress(req, res, filePath, headers) {
  const accept = req.headers["accept-encoding"] || "";
  const type = headers["Content-Type"] || "";
  const compressible =
    /^text\/|^application\/(json|xml|javascript)|^image\/svg/.test(type);

  if (!compressible) return { headers, transform: null };

  if (/\bbr\b/.test(accept)) {
    return {
      headers: { ...headers, "Content-Encoding": "br" },
      transform: createBrotli(),
    };
  }
  if (/\bgzip\b/.test(accept)) {
    return {
      headers: { ...headers, "Content-Encoding": "gzip" },
      transform: createGzip(),
    };
  }
  return { headers, transform: null };
}

function deliver(req, res, status, filePath, headers) {
  const { headers: finalHeaders, transform } = compress(req, res, filePath, headers);

  if (req.method === "HEAD") {
    res.writeHead(status, finalHeaders);
    res.end();
    return;
  }

  const source = createReadStream(filePath);
  if (!transform) {
    res.writeHead(status, finalHeaders);
    source.pipe(res);
    return;
  }

  // writeHead antes de empezar a fluir el stream.
  res.writeHead(status, finalHeaders);
  pipeline(source, transform, res, (err) => {
    if (err) {
      console.error("stream error:", err.message);
      res.destroy();
    }
  });
}

const server = createServer(async (req, res) => {
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.writeHead(405, { Allow: "GET, HEAD" });
    res.end();
    return;
  }

  const resolved = await resolveFile(req.url || "/");

  if (!resolved) {
    const notFound = await resolveFile("/404.html");
    if (!notFound) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("404 Not Found");
      return;
    }
    deliver(req, res, 404, notFound.filePath, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-cache",
    });
    return;
  }

  const ext = extname(resolved.filePath);
  const isHtml = ext === ".html";

  const headers = {
    "Content-Type": MIME[ext] || "application/octet-stream",
    // El HTML se revalida siempre; los assets se pueden cachear más tiempo.
    "Cache-Control": isHtml
      ? "no-cache"
      : "public, max-age=86400, stale-while-revalidate=604800",
    "Last-Modified": resolved.mtime.toUTCString(),
  };

  const ifModifiedSince = req.headers["if-modified-since"];
  if (
    ifModifiedSince &&
    new Date(ifModifiedSince) >= new Date(resolved.mtime.toUTCString())
  ) {
    res.writeHead(304, headers);
    res.end();
    return;
  }

  deliver(req, res, 200, resolved.filePath, headers);
});

server.listen(PORT, HOST, () => {
  console.log(`\n  Tandil Tech Week — réplica local`);
  console.log(`  → http://${HOST}:${PORT}\n`);
  console.log(`  Ctrl+C para detener\n`);
});
