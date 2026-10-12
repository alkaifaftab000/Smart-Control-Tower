from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ai_local_server
ai_local_server.load_env_file()

class handler(ai_local_server.PilotHandler):
    """Vercel serverless function entrypoint."""
    pass
