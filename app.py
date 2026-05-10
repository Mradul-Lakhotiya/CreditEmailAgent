"""
Finance Credit Follow-Up Email Agent — Streamlit Dashboard
"""

import streamlit as st
import pandas as pd

from agent.agent import load_invoices, run_agent
from agent.escalation import STAGE_CONFIG
from agent.audit_logger import get_audit_log, clear_audit_log
from agent.models import EscalationStage, AgentResult

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Credit Follow-Up Agent",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark background */
.stApp { background: #0d1117; }

/* Sidebar */
[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }

/* Metric cards */
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
}
.metric-value { font-size: 2rem; font-weight: 700; color: #e6edf3; margin: 0; }
.metric-label { font-size: 0.8rem; color: #8b949e; margin-top: 4px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-icon  { font-size: 1.5rem; margin-bottom: 8px; }

/* Stage badge */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.03em;
    white-space: nowrap;
}

/* Section headers */
.section-header {
    font-size: 1rem;
    font-weight: 600;
    color: #e6edf3;
    padding: 10px 0 6px;
    border-bottom: 1px solid #30363d;
    margin-bottom: 16px;
}

/* Email preview card */
.email-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
    margin-top: 8px;
}
.email-subject { font-size: 0.95rem; font-weight: 600; color: #58a6ff; margin-bottom: 12px; }
.email-body    { font-size: 0.85rem; color: #c9d1d9; white-space: pre-wrap; line-height: 1.7; }
.email-meta    { font-size: 0.75rem; color: #8b949e; margin-bottom: 16px; }

/* Override Streamlit button */
.stButton > button {
    background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    width: 100%;
    padding: 0.6rem;
    font-size: 0.9rem;
}
.stButton > button:hover { background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%); }

/* Scrollable invoice list */
.invoice-row {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: border-color 0.2s;
}
.invoice-row:hover { border-color: #58a6ff; }
.invoice-row.selected { border-color: #58a6ff; background: #1c2333; }

/* Dry-run pill */
.dry-run-pill {
    background: #0d419d22;
    border: 1px solid #1f6feb;
    color: #58a6ff;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    display: inline-block;
}

/* Audit table overrides */
[data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def stage_badge(stage: str) -> str:
    cfg = STAGE_CONFIG.get(EscalationStage(stage), {})
    color = cfg.get("badge_color", "#8b949e")
    bg    = cfg.get("badge_bg",    "#161b22")
    label = cfg.get("label",       stage)
    return (
        f'<span class="badge" style="color:{color};'
        f'background:{bg};border:1px solid {color};">'
        f'{label}</span>'
    )


def fmt_inr(amount: float) -> str:
    return f"₹{amount:,.0f}"


# ── Session state init ────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results: list[AgentResult] = []
if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = 0
if "agent_ran" not in st.session_state:
    st.session_state.agent_ran = False


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💳 Credit Agent")
    st.markdown('<span class="dry-run-pill">🔒 Dry-Run Mode</span>', unsafe_allow_html=True)
    st.markdown("---")

    invoices = load_invoices()

    # Stage filter
    all_stages = ["All Stages"] + [
        STAGE_CONFIG[s]["label"] for s in EscalationStage
    ]
    stage_filter = st.selectbox("Filter by Stage", all_stages)

    st.markdown("---")
    st.markdown("### Queue Summary")
    stage_counts = {}
    for inv in invoices:
        lbl = STAGE_CONFIG[inv.stage]["label"]
        stage_counts[lbl] = stage_counts.get(lbl, 0) + 1

    for lbl, cnt in stage_counts.items():
        st.markdown(f"**{lbl}** — {cnt} invoice{'s' if cnt > 1 else ''}")

    st.markdown("---")
    run_btn = st.button("⚡ Run Agent Now")
    clear_btn = st.button("🗑 Clear Audit Log")

    if clear_btn:
        clear_audit_log()
        st.session_state.results = []
        st.session_state.agent_ran = False
        st.success("Audit log cleared.")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#e6edf3;font-size:1.8rem;font-weight:700;margin-bottom:4px;'>"
    "💳 Finance Credit Follow-Up Agent</h1>"
    "<p style='color:#8b949e;font-size:0.9rem;margin-bottom:24px;'>"
    "AI-powered payment reminder engine · Gemini 1.5 Flash · Dry-Run Mode</p>",
    unsafe_allow_html=True,
)

# ── Metric Cards ──────────────────────────────────────────────────────────────
total_overdue   = len(invoices)
total_amount    = sum(inv.amount for inv in invoices)
emails_ready    = sum(1 for inv in invoices if inv.stage != EscalationStage.ESCALATED)
escalated_count = sum(1 for inv in invoices if inv.stage == EscalationStage.ESCALATED)

c1, c2, c3, c4 = st.columns(4)
cards = [
    (c1, "📋", total_overdue, "Overdue Invoices"),
    (c2, "📧", emails_ready, "Emails to Send"),
    (c3, "⚠️", escalated_count, "Escalated (Legal)"),
    (c4, "💰", fmt_inr(total_amount), "Total Outstanding"),
]
for col, icon, val, label in cards:
    with col:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-icon">{icon}</div>'
            f'<div class="metric-value">{val}</div>'
            f'<div class="metric-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Run Agent ─────────────────────────────────────────────────────────────────
if run_btn:
    filtered = invoices
    progress_bar = st.progress(0, text="Starting agent…")

    def _cb(idx, total, inv_no):
        pct = int((idx / total) * 100)
        progress_bar.progress(pct, text=f"Processing {inv_no} ({idx+1}/{total})…")

    with st.spinner("Generating emails with Gemini…"):
        st.session_state.results = run_agent(
            invoices=filtered, dry_run=True, progress_callback=_cb
        )
    progress_bar.progress(100, text="Done ✓")
    st.session_state.agent_ran = True
    st.success(f"✅ Agent completed — {len(st.session_state.results)} invoices processed.")

# ── Main Layout: Queue | Email Preview ────────────────────────────────────────
left_col, right_col = st.columns([1, 1.3], gap="large")

with left_col:
    st.markdown('<div class="section-header">📋 Invoice Queue</div>', unsafe_allow_html=True)

    # Apply stage filter
    display_invoices = invoices
    if stage_filter != "All Stages":
        display_invoices = [
            inv for inv in invoices
            if STAGE_CONFIG[inv.stage]["label"] == stage_filter
        ]

    if not display_invoices:
        st.info("No invoices match the selected filter.")
    else:
        for idx, inv in enumerate(display_invoices):
            badge = stage_badge(inv.stage.value)
            if st.button(
                f"{inv.invoice_no}  ·  {inv.client_name}  ·  {fmt_inr(inv.amount)}  ·  {inv.days_overdue}d overdue",
                key=f"inv_{idx}",
            ):
                st.session_state.selected_idx = idx

        # Small table summary
        df_display = pd.DataFrame([{
            "Invoice #":     inv.invoice_no,
            "Client":        inv.client_name,
            "Amount":        fmt_inr(inv.amount),
            "Days Overdue":  inv.days_overdue,
            "Stage":         STAGE_CONFIG[inv.stage]["label"],
        } for inv in display_invoices])

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_display, width="stretch", hide_index=True)

with right_col:
    st.markdown('<div class="section-header">📧 Email Preview</div>', unsafe_allow_html=True)

    results = st.session_state.results

    if not st.session_state.agent_ran:
        st.markdown(
            '<div class="email-card" style="text-align:center;padding:48px;">'
            '<div style="font-size:3rem;">🤖</div>'
            '<div style="color:#8b949e;margin-top:12px;">Click <b>⚡ Run Agent Now</b> in the sidebar<br>to generate emails for all overdue invoices.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif not results:
        st.info("No results yet.")
    else:
        # Invoice picker for preview
        result_options = [
            f"{r.invoice.invoice_no} — {r.invoice.client_name}" for r in results
        ]
        chosen = st.selectbox("Select invoice to preview", result_options)
        chosen_idx = result_options.index(chosen)
        result = results[chosen_idx]
        inv = result.invoice
        stage_cfg = STAGE_CONFIG[inv.stage]

        # Stage pill
        st.markdown(stage_badge(inv.stage.value), unsafe_allow_html=True)
        st.markdown(
            f'<div class="email-meta" style="margin-top:8px;">'
            f'To: {inv.contact_email} &nbsp;·&nbsp; '
            f'{inv.invoice_no} &nbsp;·&nbsp; '
            f'{fmt_inr(inv.amount)} &nbsp;·&nbsp; '
            f'{inv.days_overdue} days overdue'
            f'</div>',
            unsafe_allow_html=True,
        )

        if result.is_escalated:
            st.markdown(
                '<div class="email-card">'
                '<div style="text-align:center;padding:24px;">'
                '<div style="font-size:2.5rem;">⚠️</div>'
                '<div style="color:#a855f7;font-weight:700;font-size:1rem;margin-top:8px;">Flagged for Legal Review</div>'
                '<div style="color:#8b949e;font-size:0.85rem;margin-top:6px;">'
                'This invoice is 30+ days overdue.<br>'
                'No automated email has been sent.<br>'
                'Please assign to the finance manager or legal team.'
                '</div></div></div>',
                unsafe_allow_html=True,
            )
        elif result.error:
            st.error(f"Error generating email: {result.error}")
        elif result.email:
            email = result.email
            st.markdown(
                f'<div class="email-card">'
                f'<div class="email-subject">📌 {email.subject}</div>'
                f'<div class="email-body">{email.body}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Tone tag
            st.markdown(
                f'<div style="margin-top:10px;">'
                f'<span style="background:#1f2937;color:#58a6ff;border:1px solid #1f6feb;'
                f'border-radius:20px;padding:3px 12px;font-size:0.75rem;font-weight:600;">'
                f'Tone: {email.tone_used}</span>'
                f'&nbsp;<span style="background:#1f2937;color:#3fb950;border:1px solid #238636;'
                f'border-radius:20px;padding:3px 12px;font-size:0.75rem;font-weight:600;">'
                f'🔒 Dry-Run — Not Sent</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Audit Log ─────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">🗂 Audit Log</div>', unsafe_allow_html=True)

log = get_audit_log()
if not log:
    st.info("No audit entries yet. Run the agent to populate the log.")
else:
    df_log = pd.DataFrame(log)
    # Show key columns
    cols_show = ["timestamp", "invoice_no", "client_name", "amount", "days_overdue", "stage", "send_status", "subject"]
    df_log = df_log[[c for c in cols_show if c in df_log.columns]]
    df_log["amount"] = df_log["amount"].apply(lambda x: fmt_inr(float(x)))
    df_log["timestamp"] = pd.to_datetime(df_log["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(df_log, width="stretch", hide_index=True)
    st.caption(f"Total entries: {len(log)}")
