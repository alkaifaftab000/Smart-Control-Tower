"""Saved data for the Smart Control Tower (Postgres via DATABASE_URL).

The dashboard parses report files in the browser. This module stores those
parsed rows by production date so the same engine can recalculate any saved
day, plus the AI insights people generate. Only admins may upload or delete.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import json
import os
import re
import threading
import time

REPORT_TYPES = ("production", "downtime", "rejection")
INSIGHT_KINDS = ("daily", "monthly", "question", "chat")
MAX_ROWS_PER_CHUNK = 2000
SESSION_SECONDS = 12 * 3600
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS uploads (
  id BIGSERIAL PRIMARY KEY,
  report_type TEXT NOT NULL CHECK (report_type IN ('production','downtime','rejection')),
  file_name TEXT NOT NULL,
  uploaded_by TEXT NOT NULL,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','active','deleted')),
  row_count INTEGER NOT NULL,
  dates DATE[] NOT NULL,
  issues JSONB NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS report_rows (
  id BIGSERIAL PRIMARY KEY,
  upload_id BIGINT NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
  report_type TEXT NOT NULL,
  production_date DATE NOT NULL,
  data JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS report_rows_type_date ON report_rows (report_type, production_date);
CREATE INDEX IF NOT EXISTS report_rows_upload ON report_rows (upload_id);
CREATE TABLE IF NOT EXISTS insights (
  id BIGSERIAL PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('daily','monthly','question','chat')),
  period TEXT NOT NULL DEFAULT '',
  question TEXT NOT NULL DEFAULT '',
  answer TEXT NOT NULL DEFAULT '',
  payload JSONB NOT NULL DEFAULT '{}',
  tags TEXT[] NOT NULL DEFAULT '{}',
  data_key TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS insights_one_review ON insights (kind, period) WHERE kind IN ('daily','monthly');
CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  at TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  detail JSONB NOT NULL DEFAULT '{}'
);
"""


class StoreError(Exception):
    def __init__(self, status: int, message: str, extra: dict | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.extra = extra or {}


_conn = None
_conn_used = 0.0
_conn_lock = threading.Lock()


def configured() -> bool:
    return bool(os.environ.get("DATABASE_URL", "").strip())


def _open():
    if not configured():
        raise StoreError(503, "Saved data is not set up: DATABASE_URL is missing.")
    import psycopg  # imported here so the AI-only server still runs without it

    # Keepalives, so a dropped connection fails fast instead of hanging.
    conn = psycopg.connect(os.environ["DATABASE_URL"].strip(), connect_timeout=15, keepalives=1,
                           keepalives_idle=20, keepalives_interval=5, keepalives_count=3)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


@contextlib.contextmanager
def connect():
    """One reused connection per process (opening one costs seconds over a long
    network path); requests take turns. After a quiet minute a fresh connection is
    opened, because the database silently closes idle ones and a check on a dead
    connection can hang."""
    global _conn, _conn_used
    with _conn_lock:
        if _conn is None or _conn.closed or _conn.broken:
            _conn = _open()
        elif time.time() - _conn_used > 60:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = _open()
        try:
            yield _conn
            _conn_used = time.time()
        except BaseException:
            if not _conn.closed:
                _conn.rollback()
            raise


# ---------- login (signed token, no server-side session) ----------
# Two accounts from the environment: a viewer (dashboard, AI, insights) and an
# admin (also uploads and deletes saved days).

ROLES = ("viewer", "admin")


def _accounts() -> dict:
    out = {}
    for role in ROLES:
        email = os.environ.get(f"{role.upper()}_EMAIL", "").strip().lower()
        password = os.environ.get(f"{role.upper()}_PASSWORD", "")
        if email and password:
            out[role] = (email, password)
    return out


def login_required() -> bool:
    """Viewing is public unless VIEW_REQUIRES_LOGIN=1; uploading and deleting always need the admin."""
    return os.environ.get("VIEW_REQUIRES_LOGIN", "").strip() == "1" and bool(_accounts())


def demo_accounts() -> list[dict]:
    """Shown on the login screen only when DEMO_LOGIN_HINT=1 (pilot demos)."""
    if os.environ.get("DEMO_LOGIN_HINT", "").strip() != "1":
        return []
    return [{"role": r, "email": e, "password": p} for r, (e, p) in _accounts().items()]


def _session_key() -> bytes:
    secret = os.environ.get("SESSION_SECRET") or "|".join(p for _, p in _accounts().values()) + os.environ.get("DATABASE_URL", "")
    return hashlib.sha256(secret.encode("utf-8")).digest()


def _sign(body: str) -> str:
    return hmac.new(_session_key(), body.encode(), hashlib.sha256).hexdigest()


def login(email: str, password: str) -> dict:
    accounts = _accounts()
    if not accounts:
        raise StoreError(503, "Login is not set up: add ADMIN_EMAIL and ADMIN_PASSWORD.")
    email = str(email).strip().lower()
    for role, (want_email, want_pass) in accounts.items():
        email_ok = hmac.compare_digest(email.encode(), want_email.encode())
        pass_ok = hmac.compare_digest(str(password).encode(), want_pass.encode())
        if email_ok and pass_ok:
            expires = int(time.time()) + SESSION_SECONDS
            body = f"{role}|{want_email}|{expires}"
            token = base64.urlsafe_b64encode(f"{body}|{_sign(body)}".encode()).decode()
            return {"token": token, "role": role, "email": want_email, "expires": expires}
    time.sleep(0.5)
    raise StoreError(401, "Wrong email or password.")


def user_from_header(header: str, need: str = "viewer") -> dict:
    """Check a 'Bearer <token>' header. need='admin' also requires the admin role."""
    token = header[7:].strip() if header.startswith("Bearer ") else ""
    try:
        role, email, expires, sig = base64.urlsafe_b64decode(token.encode()).decode().split("|")
        valid = (hmac.compare_digest(sig, _sign(f"{role}|{email}|{expires}")) and int(expires) > time.time()
                 and _accounts().get(role, ("",))[0] == email)
    except (ValueError, UnicodeDecodeError):
        valid = False
    if not valid:
        raise StoreError(401, "Please log in.")
    if need == "admin" and role != "admin":
        raise StoreError(403, "Only the admin can upload or delete data.")
    return {"role": role, "email": email}


# ---------- reading saved data ----------

def summary(conn) -> dict:
    """Months and days with saved data, which upload holds each day, and the upload log."""
    days: dict[str, dict] = {}
    for date, rtype, upload_id, rows in conn.execute(
        """SELECT r.production_date, r.report_type, r.upload_id, count(*)
           FROM report_rows r JOIN uploads u ON u.id = r.upload_id
           WHERE u.status = 'active'
           GROUP BY 1, 2, 3 ORDER BY 1"""
    ):
        days.setdefault(date.isoformat(), {})[rtype] = {"upload": upload_id, "rows": rows}
    uploads = [
        {"id": i, "type": t, "file": f, "by": b, "at": a.isoformat(), "rows": n,
         "from": min(d).isoformat() if d else None, "to": max(d).isoformat() if d else None, "issues": iss}
        for i, t, f, b, a, n, d, iss in conn.execute(
            """SELECT id, report_type, file_name, uploaded_by, uploaded_at, row_count, dates, issues
               FROM uploads WHERE status = 'active' ORDER BY uploaded_at DESC"""
        )
    ]
    months = sorted({d[:7] for d in days})
    return {"days": days, "months": months, "uploads": uploads}


def data_version(conn) -> str:
    """Changes whenever an upload is saved or a day is deleted (both write the audit log)."""
    (last,) = conn.execute("SELECT coalesce(max(id), 0) FROM audit_log").fetchone()
    return str(last)


def month_rows(conn, month: str) -> dict:
    if not MONTH_RE.match(month or ""):
        raise StoreError(400, "Month must look like 2026-10.")
    out: dict[str, list] = {t: [] for t in REPORT_TYPES}
    for rtype, data in conn.execute(
        """SELECT r.report_type, r.data FROM report_rows r JOIN uploads u ON u.id = r.upload_id
           WHERE u.status = 'active' AND to_char(r.production_date, 'YYYY-MM') = %s
           ORDER BY r.id""",
        (month,),
    ):
        out[rtype].append(data)
    return out


# ---------- uploading (admin) ----------

def _clean_dates(dates) -> list[str]:
    if not isinstance(dates, list) or not dates or not all(isinstance(d, str) and DATE_RE.match(d) for d in dates):
        raise StoreError(400, "The file has no valid production dates.")
    return sorted(set(dates))


def _already_saved(conn, report_type: str, dates: list[str]) -> list[str]:
    return [
        d.isoformat()
        for (d,) in conn.execute(
            """SELECT DISTINCT r.production_date FROM report_rows r JOIN uploads u ON u.id = r.upload_id
               WHERE u.status = 'active' AND r.report_type = %s AND r.production_date = ANY(%s::date[])
               ORDER BY 1""",
            (report_type, dates),
        )
    ]


def _conflict(report_type: str, taken: list[str]) -> StoreError:
    shown = ", ".join(taken[:6]) + (f" and {len(taken) - 6} more" if len(taken) > 6 else "")
    return StoreError(
        409,
        f"Already uploaded: {report_type} data for {shown} is already saved. Nothing was saved from this file. "
        "To replace it, delete those days first.",
        {"dates": taken},
    )


def begin_upload(conn, admin: str, body: dict) -> dict:
    report_type = body.get("reportType")
    if report_type not in REPORT_TYPES:
        raise StoreError(400, "Unknown report type.")
    dates = _clean_dates(body.get("dates"))
    row_count = body.get("rowCount")
    if not isinstance(row_count, int) or row_count < 1:
        raise StoreError(400, "The file has no rows to save.")
    issues = [str(x)[:300] for x in (body.get("issues") or [])[:60]]
    # Unfinished uploads older than an hour were abandoned (closed tab, lost network).
    conn.execute("DELETE FROM uploads WHERE status = 'pending' AND uploaded_at < now() - interval '1 hour'")
    taken = _already_saved(conn, report_type, dates)
    if taken:
        raise _conflict(report_type, taken)
    (upload_id,) = conn.execute(
        """INSERT INTO uploads (report_type, file_name, uploaded_by, row_count, dates, issues)
           VALUES (%s, %s, %s, %s, %s::date[], %s) RETURNING id""",
        (report_type, str(body.get("fileName") or "file")[:200], admin, row_count, dates, json.dumps(issues)),
    ).fetchone()
    conn.commit()
    return {"uploadId": upload_id}


def _pending_upload(conn, upload_id) -> tuple[str, int, list]:
    row = conn.execute(
        "SELECT report_type, row_count, dates FROM uploads WHERE id = %s AND status = 'pending'", (upload_id,)
    ).fetchone()
    if not row:
        raise StoreError(404, "This upload has expired or was already finished. Upload the file again.")
    return row


def add_rows(conn, body: dict) -> dict:
    upload_id = body.get("uploadId")
    rows = body.get("rows")
    report_type, _, dates = _pending_upload(conn, upload_id)
    allowed = {d.isoformat() for d in dates}
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS_PER_CHUNK:
        raise StoreError(400, "Invalid batch of rows.")
    if any(not isinstance(r, dict) or r.get("date") not in allowed for r in rows):
        raise StoreError(400, "A row has a date that was not declared for this upload.")
    # One statement per batch: row-by-row inserts take minutes over a remote connection.
    conn.execute(
        """INSERT INTO report_rows (upload_id, report_type, production_date, data)
           SELECT %s, %s, (e->>'date')::date, e FROM jsonb_array_elements(%s::jsonb) WITH ORDINALITY AS t(e, n)
           ORDER BY n""",
        (upload_id, report_type, json.dumps(rows)),
    )
    conn.commit()
    return {"saved": len(rows)}


def commit_upload(conn, admin: str, body: dict) -> dict:
    upload_id = body.get("uploadId")
    report_type, row_count, dates = _pending_upload(conn, upload_id)
    (saved,) = conn.execute("SELECT count(*) FROM report_rows WHERE upload_id = %s", (upload_id,)).fetchone()
    if saved != row_count:
        conn.execute("DELETE FROM uploads WHERE id = %s", (upload_id,))
        conn.commit()
        raise StoreError(500, f"Only {saved} of {row_count} rows arrived, so nothing was saved. Upload the file again.")
    # Lock per report type so two admins cannot save the same day at once.
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("upload:" + report_type,))
    taken = _already_saved(conn, report_type, [d.isoformat() for d in dates])
    if taken:
        conn.execute("DELETE FROM uploads WHERE id = %s", (upload_id,))
        conn.commit()
        raise _conflict(report_type, taken)
    conn.execute("UPDATE uploads SET status = 'active' WHERE id = %s", (upload_id,))
    conn.execute(
        "INSERT INTO audit_log (actor, action, detail) VALUES (%s, 'upload', %s)",
        (admin, json.dumps({"uploadId": upload_id, "type": report_type, "rows": row_count})),
    )
    conn.commit()
    return {"uploadId": upload_id, "rows": row_count}


def abort_upload(conn, body: dict) -> dict:
    conn.execute("DELETE FROM uploads WHERE id = %s AND status = 'pending'", (body.get("uploadId"),))
    conn.commit()
    return {"ok": True}


def delete_day(conn, admin: str, body: dict) -> dict:
    date, report_type = body.get("date"), body.get("reportType")
    if not isinstance(date, str) or not DATE_RE.match(date) or report_type not in REPORT_TYPES:
        raise StoreError(400, "Choose a date and a report type to delete.")
    deleted = conn.execute(
        """DELETE FROM report_rows r USING uploads u
           WHERE u.id = r.upload_id AND u.status = 'active' AND r.report_type = %s AND r.production_date = %s""",
        (report_type, date),
    ).rowcount
    if not deleted:
        raise StoreError(404, f"No saved {report_type} data for {date}.")
    # An upload with no rows left no longer holds any day.
    conn.execute(
        """UPDATE uploads u SET status = 'deleted' WHERE u.status = 'active'
           AND NOT EXISTS (SELECT 1 FROM report_rows r WHERE r.upload_id = u.id)"""
    )
    conn.execute(
        "INSERT INTO audit_log (actor, action, detail) VALUES (%s, 'delete_day', %s)",
        (admin, json.dumps({"date": date, "type": report_type, "rows": deleted})),
    )
    conn.commit()
    return {"deleted": deleted}


# ---------- insights (anyone) ----------

def list_insights(conn) -> list[dict]:
    return [
        {"id": i, "kind": k, "period": p, "question": q, "answer": a, "payload": pl, "tags": t, "dataKey": dk, "at": at.isoformat()}
        for i, k, p, q, a, pl, t, dk, at in conn.execute(
            """SELECT id, kind, period, question, answer, payload, tags, data_key, created_at
               FROM insights ORDER BY created_at DESC LIMIT 500"""
        )
    ]


def save_insight(conn, body: dict) -> dict:
    kind = body.get("kind")
    if kind not in INSIGHT_KINDS:
        raise StoreError(400, "Unknown insight kind.")
    period = str(body.get("period") or "")[:20]
    if kind in ("daily", "question") and not DATE_RE.match(period):
        raise StoreError(400, "A daily insight needs a date.")
    if kind == "monthly" and not MONTH_RE.match(period):
        raise StoreError(400, "A monthly insight needs a month.")
    tags = sorted({str(t).strip()[:60] for t in (body.get("tags") or [])[:30] if str(t).strip()})
    values = (
        kind, period, str(body.get("question") or "")[:4000], str(body.get("answer") or "")[:60000],
        json.dumps(body.get("payload") if isinstance(body.get("payload"), dict) else {}),
        tags, str(body.get("dataKey") or "")[:500],
    )
    if kind in ("daily", "monthly"):
        # One saved review per day or month: a newer run replaces the older one.
        sql = """INSERT INTO insights (kind, period, question, answer, payload, tags, data_key)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)
                 ON CONFLICT (kind, period) WHERE kind IN ('daily','monthly')
                 DO UPDATE SET question = EXCLUDED.question, answer = EXCLUDED.answer, payload = EXCLUDED.payload,
                   tags = EXCLUDED.tags, data_key = EXCLUDED.data_key, created_at = now()
                 RETURNING id"""
    else:
        sql = """INSERT INTO insights (kind, period, question, answer, payload, tags, data_key)
                 VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id"""
    (insight_id,) = conn.execute(sql, values).fetchone()
    conn.commit()
    return {"id": insight_id}

