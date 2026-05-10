from datetime import date
from typing import List

import pandas as pd

from .config import DATA_PATH
from .models import Invoice, EmailDraft, AgentResult, EscalationStage
from .escalation import determine_stage
from .email_generator import generate_email
from .audit_logger import get_cached_email, log_email, log_escalation


def load_invoices() -> List[Invoice]:
    """Read invoices.csv and return all overdue Invoice objects sorted by days overdue desc."""
    df = pd.read_csv(DATA_PATH)
    invoices: List[Invoice] = []
    today = date.today()

    for _, row in df.iterrows():
        due_date = pd.to_datetime(row["due_date"]).date()
        days_overdue = (today - due_date).days

        if days_overdue < 1:
            continue  # Not yet overdue

        stage = determine_stage(days_overdue)
        invoices.append(
            Invoice(
                invoice_no=str(row["invoice_no"]),
                client_name=str(row["client_name"]),
                client_company=str(row["client_company"]),
                amount=float(row["amount"]),
                currency=str(row.get("currency", "INR")),
                due_date=due_date,
                contact_email=str(row["contact_email"]),
                follow_up_count=int(row.get("follow_up_count", 0)),
                payment_link=str(row["payment_link"]),
                days_overdue=days_overdue,
                stage=stage,
            )
        )

    return sorted(invoices, key=lambda inv: inv.days_overdue, reverse=True)


def run_agent(
    invoices: List[Invoice] | None = None,
    dry_run: bool = True,
    progress_callback=None,
) -> List[AgentResult]:
    """
    Main agent loop.
    - Escalated invoices are flagged (no email sent).
    - All others get an LLM-generated email logged to SQLite.
    - progress_callback(i, total, invoice_no) is called per invoice if provided.
    """
    if invoices is None:
        invoices = load_invoices()

    results: List[AgentResult] = []

    for idx, invoice in enumerate(invoices):
        if progress_callback:
            progress_callback(idx, len(invoices), invoice.invoice_no)

        if invoice.stage == EscalationStage.ESCALATED:
            log_escalation(invoice)
            results.append(AgentResult(invoice=invoice, is_escalated=True))
        else:
            cached = get_cached_email(invoice)
            if cached is not None:
                email = cached["email"]
                prev_status = cached["send_status"]
                if prev_status == "sent" or dry_run:
                    results.append(AgentResult(invoice=invoice, email=email))
                    continue
                # If we have a dry-run cached email but the current run should actually send,
                # reuse the generated draft and log the send.
                if prev_status == "dry_run" and not dry_run:
                    send_status = "sent"
                    log_email(invoice, email, send_status)
                    results.append(AgentResult(invoice=invoice, email=email))
                    continue

            try:
                email = generate_email(invoice)
                send_status = "dry_run" if dry_run else "sent"
                log_email(invoice, email, send_status)
                results.append(AgentResult(invoice=invoice, email=email))
            except Exception as exc:
                results.append(
                    AgentResult(invoice=invoice, error=str(exc))
                )

    return results
