"""Vercel entry point: every /api/* request runs the same handler as the local server."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server

server.load_env_file()


class handler(server.PilotHandler):
    pass


app = handler
