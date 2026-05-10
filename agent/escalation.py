from .models import EscalationStage

# Stage metadata: tone, message, CTA, UI color
STAGE_CONFIG = {
    EscalationStage.STAGE_1: {
        "label":       "1st Follow-Up",
        "tone":        "Warm & Friendly",
        "key_message": "Gentle reminder — assume it was an oversight",
        "cta":         "Please use the payment link below to settle at your earliest convenience.",
        "days_range":  (1, 7),
        "badge_color": "#4ade80",   # green
        "badge_bg":    "#052e16",
    },
    EscalationStage.STAGE_2: {
        "label":       "2nd Follow-Up",
        "tone":        "Polite but Firm",
        "key_message": "Payment still pending — request confirmation of payment date",
        "cta":         "Please confirm the payment date or process the payment using the link below.",
        "days_range":  (8, 14),
        "badge_color": "#facc15",   # yellow
        "badge_bg":    "#1a1400",
    },
    EscalationStage.STAGE_3: {
        "label":       "3rd Follow-Up",
        "tone":        "Formal & Serious",
        "key_message": "Escalating concern — continued non-payment may impact credit terms",
        "cta":         "Please respond within 48 hours with a payment confirmation or contact our accounts team immediately.",
        "days_range":  (15, 21),
        "badge_color": "#fb923c",   # orange
        "badge_bg":    "#1c0a00",
    },
    EscalationStage.STAGE_4: {
        "label":       "4th Follow-Up",
        "tone":        "Stern & Urgent",
        "key_message": "Final reminder before legal escalation",
        "cta":         "Pay immediately via the link below or call our accounts team. Failure to act within 24 hours will result in escalation to our legal team.",
        "days_range":  (22, 30),
        "badge_color": "#f87171",   # red
        "badge_bg":    "#1c0000",
    },
    EscalationStage.ESCALATED: {
        "label":       "⚠ Legal Escalation",
        "tone":        "Flag for Legal Review",
        "key_message": "Human review required — no automated email sent",
        "cta":         "Assign to finance manager / legal team",
        "days_range":  (31, 9999),
        "badge_color": "#a855f7",   # purple
        "badge_bg":    "#1a0030",
    },
}


def determine_stage(days_overdue: int) -> EscalationStage:
    """Map days overdue to the correct escalation stage."""
    if days_overdue <= 7:
        return EscalationStage.STAGE_1
    elif days_overdue <= 14:
        return EscalationStage.STAGE_2
    elif days_overdue <= 21:
        return EscalationStage.STAGE_3
    elif days_overdue <= 30:
        return EscalationStage.STAGE_4
    else:
        return EscalationStage.ESCALATED
