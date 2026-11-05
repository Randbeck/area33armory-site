#!/usr/bin/env python3
"""Serve a staged approved-only Area 33 catalog on LOOPBACK for local review.

No production server, live upload, auto-start, public binding, or private
rights reports are exposed. Ctrl+C stops the server.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path


class PrivatePreviewError(ValueError):
    pass


class LocalCatalogHandler(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(404, "Directory listings disabled")
        return None

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()


def make_server(preview_root: Path, port: int = 8765) -> ThreadingHTTPServer:
    preview_root=Path(preview_root).expanduser().resolve()
    report=preview_root/"preflight-private-report.json"
    site=preview_root/"site"
    if (not report.is_file() or report.is_symlink() or
            not site.is_dir() or site.is_symlink()):
        raise PrivatePreviewError("Expected a validated private site staging folder")
    status=json.loads(report.read_text(encoding="utf-8"))
    if (status.get("schema")!="area33.private_site_release_preflight.v1" or
            status.get("private_preview_only") is not True or
            status.get("deployed") is not False or
            status.get("site_modified") is not False):
        raise PrivatePreviewError("Preflight report is not marked private-only")
    if not (site/"catalog.html").is_file() or not (
        site/"assets/catalog-index.v2.json"
    ).is_file():
        raise PrivatePreviewError("Private site catalog preview is incomplete")
    if type(port) is not int or not 0 <= port <= 65535:
        raise PrivatePreviewError("Invalid loopback port")
    handler=partial(LocalCatalogHandler,directory=str(site))
    return ThreadingHTTPServer(("127.0.0.1",port),handler)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preview-root",type=Path,required=True)
    p.add_argument("--port",type=int,default=8765)
    p.add_argument("--serve-private-preview",action="store_true")
    args=p.parse_args(argv)
    if not args.serve_private_preview:
        p.error("Explicit --serve-private-preview required")
    try:
        server=make_server(args.preview_root,args.port)
    except (OSError,ValueError) as exc:
        p.error(str(exc))
    url=f"http://127.0.0.1:{server.server_address[1]}/catalog.html"
    print("PRIVATE Area 33 website preview. NO INTERNET PUBLICATION.")
    print("Open:",url)
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Private preview stopped.")
    finally:
        server.server_close()


if __name__=="__main__":
    main()
