"""Simple in-memory store for demo data."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4


class FakeDB:
    def __init__(self) -> None:
        self.users: Dict[str, dict] = {}
        self.sources: Dict[str, dict] = {}
        self.branding: dict = {
            "organization": "Sentiment Dash",
            "primary_color": "#0055FF",
            "logo_url": "https://example.com/logo.png",
            "template": {
                "header": "Sentiment Dash Report",
                "footer": "Confidential"
            },
        }
        self.reports: Dict[str, dict] = {}
        self.tokens: Dict[str, dict] = {}
        self.audit_logs: List[dict] = []
        self.roles: Dict[str, dict] = {
            "admin": {"name": "Administrator", "permissions": ["*"]},
            "analyst": {"name": "Analyst", "permissions": ["read", "export"]},
        }
        self._seed_data()

    def _seed_data(self) -> None:
        admin_id = str(uuid4())
        analyst_id = str(uuid4())
        self.users[admin_id] = {
            "id": admin_id,
            "username": "admin",
            "full_name": "Admin User",
            "role": "admin",
            "email": "admin@example.com",
            "created_at": datetime.utcnow(),
        }
        self.users[analyst_id] = {
            "id": analyst_id,
            "username": "analyst",
            "full_name": "Content Analyst",
            "role": "analyst",
            "email": "analyst@example.com",
            "created_at": datetime.utcnow(),
        }
        rss_id = str(uuid4())
        self.sources[rss_id] = {
            "id": rss_id,
            "name": "Default RSS",
            "type": "rss",
            "config": {"url": "https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id"},
            "status": "active",
            "last_run": datetime.utcnow(),
        }

    # ---------- User helpers ----------

    def validate_user(self, username: str, password: str) -> Optional[dict]:
        # Demo only: username must match password
        for user in self.users.values():
            if user["username"] == username and password == username:
                return user
        return None

    def add_user(self, payload: dict) -> dict:
        user_id = str(uuid4())
        data = {**payload, "id": user_id, "created_at": datetime.utcnow()}
        self.users[user_id] = data
        self._log("user_create", f"User {user_id} created")
        return data

    def update_user(self, user_id: str, payload: dict) -> dict:
        user = self.users[user_id]
        user.update(payload)
        self._log("user_update", f"User {user_id} updated")
        return user

    def delete_user(self, user_id: str) -> None:
        self.users.pop(user_id, None)
        self._log("user_delete", f"User {user_id} deleted")

    def issue_token(self, user_id: str, expires_in: int = 3600) -> dict:
        token = str(uuid4())
        data = {"token": token, "user_id": user_id, "expires_at": datetime.utcnow()}
        self.tokens[token] = data
        self._log("auth_login", f"Token issued for user {user_id}")
        return data

    def revoke_token(self, token: str) -> None:
        self.tokens.pop(token, None)
        self._log("auth_logout", f"Token revoked")

    def log_report_job(self, payload: dict) -> dict:
        report_id = str(uuid4())
        data = {"id": report_id, **payload, "status": "ready", "generated_at": datetime.utcnow()}
        self.reports[report_id] = data
        self._log("report_generate", f"Report {report_id} generated")
        return data

    def _log(self, action: str, message: str) -> None:
        self.audit_logs.append(
            {
                "id": str(uuid4()),
                "action": action,
                "message": message,
                "timestamp": datetime.utcnow(),
            }
        )


fake_db = FakeDB()
