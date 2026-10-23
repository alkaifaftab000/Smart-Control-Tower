from __future__ import annotations
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import server as ai_local_server
ai_local_server.load_env_file()

class handler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Local-AI-Token")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.end_headers()

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

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > ai_local_server.MAX_BODY_BYTES:
                raise ai_local_server.ProviderError(413, "Request is empty or too large.")
            
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            messages = body.get("messages") if isinstance(body, dict) else None
            if not isinstance(messages, list) or not 1 <= len(messages) <= 14:
                raise ai_local_server.ProviderError(400, "Conversation is invalid or too long.")
            
            result = ai_local_server.handle_question(messages)
            resp_bytes = json.dumps(result, ensure_ascii=False).encode("utf-8")
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
        except ai_local_server.ProviderError as pe:
            err_bytes = json.dumps({"error": pe.message}, ensure_ascii=False).encode("utf-8")
            self.send_response(pe.status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err_bytes)))
            self.end_headers()
            self.wfile.write(err_bytes)
        except Exception as e:
            err_bytes = json.dumps({"error": f"Internal server error: {str(e)}"}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err_bytes)))
            self.end_headers()
            self.wfile.write(err_bytes)

app = handler
