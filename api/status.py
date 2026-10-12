from __future__ import annotations
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ai_local_server
ai_local_server.load_env_file()

class handler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self) -> None:
        primary = bool(ai_local_server.key_for("OPENAI_API_KEY"))
        mistral = bool(ai_local_server.key_for("MISTRAL_API_KEY"))
        groq = bool(ai_local_server.key_for("GROQ_API_KEY"))
        
        data = {
            "openai": primary or mistral or groq,
            "primaryOpenAI": primary,
            "mistral": mistral,
            "groq": groq
        }
        resp_bytes = json.dumps(data).encode("utf-8")
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)
