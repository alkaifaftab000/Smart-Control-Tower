"""Vercel entry point: every /api/* request runs the same handler as the local server."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server

server.load_env_file()


class handler(server.PilotHandler):
    def restore_path(self) -> None:
        """vercel.json sends every /api/* request here as /api/index.py?__path=<original path>."""
        parts = urlsplit(self.path)
        query = parse_qsl(parts.query, keep_blank_values=True)
        original = next((v for k, v in query if k == "__path"), "")
        if original.startswith("/api/"):
            rest = urlencode([(k, v) for k, v in query if k != "__path"])
            self.path = original + ("?" + rest if rest else "")

    def do_GET(self) -> None:
        self.restore_path()
        super().do_GET()

    def do_POST(self) -> None:
        self.restore_path()
        super().do_POST()


app = handler
