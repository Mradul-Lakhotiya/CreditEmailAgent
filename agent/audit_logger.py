import sqlite3
from datetime import datetime
from typing import List, Dict, Any

from .config import DB_PATH
from .models import Invoice, EmailDraft, EscalationStage


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH))


def init_db() -> None:
    """Create audit table if it doesn't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no      TEXT    NOT NULL,
            client_name     TEXT    NOT NULL,
            client_company  TEXT    NOT NULL,
            amount          REAL    NOT NULL,
            days_overdue    INTEGER NOT NULL,
            stage           TEXT    NOT NULL,
            subject         TEXT,
            body            TEXT,
            tone_used       TEXT,
            send_status     TEXT    NOT NULL,
            timestamp       TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_email(invoice: Invoice, email: EmailDraft, send_status: str = "dry_run") -> None:
    init_db()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO audit_log
           (invoice_no, client_name, client_company, amount, days_overdue,
            stage, subject, body, tone_used, send_status, timestamp)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            invoice.invoice_no, invoice.client_name, invoice.client_company,
            invoice.amount, invoice.days_overdue, invoice.stage.value,
            email.subject, email.body, email.tone_used,
            send_status, datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def log_escalation(invoice: Invoice) -> None:
    init_db()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO audit_log
           (invoice_no, client_name, client_company, amount, days_overdue,
            stage, subject, body, tone_used, send_status, timestamp)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            invoice.invoice_no, invoice.client_name, invoice.client_company,
            invoice.amount, invoice.days_overdue, "escalated",
            "FLAGGED FOR LEGAL REVIEW",
            f"Invoice {invoice.invoice_no} ({invoice.days_overdue} days overdue) "
            f"has been escalated to the finance/legal team for manual review.",
            "Legal Escalation",
            "escalated",
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_audit_log() -> List[Dict[str, Any]]:
    init_db()
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cached_email(invoice: Invoice):
    init_db()
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """SELECT subject, body, tone_used, send_status
           FROM audit_log
           WHERE invoice_no = ? AND stage = ? AND send_status IN ('dry_run', 'sent')
           ORDER BY timestamp DESC
           LIMIT 1""",
        (invoice.invoice_no, invoice.stage.value),
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "email": EmailDraft(
            subject=row["subject"],
            body=row["body"],
            tone_used=row["tone_used"],
        ),
        "send_status": row["send_status"],
    }


def clear_audit_log() -> None:
    init_db()
    conn = _get_conn()
    conn.execute("DELETE FROM audit_log")
    conn.commit()
    conn.close()
