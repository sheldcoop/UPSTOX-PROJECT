"""Webhook Service - Signature verification and idempotency"""

from typing import Dict, Any, Optional
import hashlib
import hmac
import json
import os
import sqlite3
import time


class WebhookService:
    """Handles incoming webhook validation and idempotency tracking"""

    def __init__(self, db_path: str = "market_data.db", secret: Optional[str] = None):
        self.db_path = db_path
        self.secret = secret or os.getenv("UPSTOX_WEBHOOK_SECRET") or os.getenv("WEBHOOK_SECRET")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                received_at REAL,
                status TEXT,
                payload TEXT
            )
        """
        )
        conn.commit()
        conn.close()

    def _header_value(self, headers: Dict[str, Any], name: str) -> Optional[str]:
        for key, value in headers.items():
            if key.lower() == name.lower():
                return value
        return None

    def _compute_event_id(self, raw_body: bytes, headers: Dict[str, Any]) -> str:
        event_id = (
            self._header_value(headers, "X-Upstox-Event-Id")
            or self._header_value(headers, "X-Event-Id")
            or self._header_value(headers, "X-Request-Id")
        )
        if event_id:
            return event_id
        return hashlib.sha256(raw_body).hexdigest()

    def verify_signature(self, raw_body: bytes, headers: Dict[str, Any]) -> bool:
        if not self.secret:
            return True

        signature = (
            self._header_value(headers, "X-Upstox-Signature")
            or self._header_value(headers, "X-Signature")
            or self._header_value(headers, "X-Hub-Signature-256")
        )
        if not signature:
            return False

        if signature.startswith("sha256="):
            signature = signature.split("=", 1)[1]

        expected = hmac.new(
            self.secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    def _is_duplicate(self, event_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM webhook_events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def _record_event(self, event_id: str, payload_text: str, status: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO webhook_events (event_id, received_at, status, payload)
            VALUES (?, ?, ?, ?)
        """,
            (event_id, time.time(), status, payload_text),
        )
        conn.commit()
        conn.close()

    def receive(self, raw_body: bytes, headers: Dict[str, Any]) -> Dict[str, Any]:
        if not self.verify_signature(raw_body, headers):
            raise ValueError("Invalid webhook signature")

        event_id = self._compute_event_id(raw_body, headers)
        if self._is_duplicate(event_id):
            return {"status": "duplicate", "event_id": event_id}

        payload_text = raw_body.decode("utf-8", errors="replace")
        status = "accepted"
        try:
            json.loads(payload_text)
        except Exception:
            status = "accepted_unparsed"

        self._record_event(event_id, payload_text, status)
        return {"status": status, "event_id": event_id}

    def receive_update(self, raw_body: bytes, headers: Dict[str, Any]) -> Dict[str, Any]:
        return self.receive(raw_body, headers)
