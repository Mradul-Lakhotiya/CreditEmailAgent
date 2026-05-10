from pydantic import BaseModel
from datetime import date
from typing import Optional
from enum import Enum


class EscalationStage(str, Enum):
    STAGE_1 = "stage_1"      # 1–7 days overdue
    STAGE_2 = "stage_2"      # 8–14 days overdue
    STAGE_3 = "stage_3"      # 15–21 days overdue
    STAGE_4 = "stage_4"      # 22–30 days overdue
    ESCALATED = "escalated"  # 30+ days → legal flag


class Invoice(BaseModel):
    invoice_no: str
    client_name: str
    client_company: str
    amount: float
    currency: str = "INR"
    due_date: date
    contact_email: str
    follow_up_count: int = 0
    payment_link: str
    days_overdue: int = 0
    stage: Optional[EscalationStage] = None


class EmailDraft(BaseModel):
    subject: str
    body: str
    tone_used: str


class AgentResult(BaseModel):
    invoice: Invoice
    email: Optional[EmailDraft] = None
    is_escalated: bool = False
    error: Optional[str] = None
