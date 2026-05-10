# Presentation Deck Outline (8-10 Slides)

**Slide 1: Title Slide**
- Project Title: Finance Credit Follow-Up Email Agent
- Your Name
- Date / AI Enablement Internship

**Slide 2: The Business Problem**
- Finance teams spend significant time manually chasing overdue payments.
- Manual follow-ups lead to inconsistent tone, missed timings, and potential strain on client relationships.
- High DSO (Days Sales Outstanding) impacts cash flow.

**Slide 3: The Solution**
- An AI-powered agent that automates payment reminders.
- Intelligently escalates urgency based on the number of days overdue.
- Maintains a professional tone, logs all interactions for audit, and flags severe cases for manual legal review.

**Slide 4: Agent Architecture**
- Data Ingestion: Reads pending credits from CSV.
- Tone Escalation Engine: Rule-based routing to determine the correct stage (Stage 1 to 4, or Escalated).
- Email Generation: Gemini 1.5 Flash generates tailored, personalised emails.
- Audit Trail: All actions logged locally to SQLite.
- *(Include the Mermaid diagram from README here.)*

**Slide 5: Escalation Matrix**
- **Stage 1 (1-7 days):** Warm & Friendly
- **Stage 2 (8-14 days):** Polite but Firm
- **Stage 3 (15-21 days):** Formal & Serious
- **Stage 4 (22-30 days):** Stern & Urgent
- **Escalated (30+ days):** Flagged for Legal Review (No automated email sent)

**Slide 6: Technology Stack**
- **LLM:** Google `models/gemini-2.5-flash` (Cost-effective, fast, great JSON output).
- **Backend:** Python + Pandas (Data Handling) + SQLite (Audit Logging).
- **UI/Dashboard:** Streamlit (Rapid prototyping, interactive).
- **Mode:** Dry-Run Mode for safe testing.

**Slide 7: Security & Risk Mitigation**
- **API Key Protection:** `.env` file, not committed to code.
- **Hallucination Control:** Low temperature (0.3), strict JSON output formatting, deterministic rule-based escalation.
- **Email Spoofing/Accidental Sends:** Default Dry-Run mode ensures no real emails are sent during testing.
- **Prompt Injection:** Strict templating and input sanitisation.

**Slide 8: Demo Walkthrough**
- *(Place a placeholder for your video or live demo link here)*
- Highlight the Streamlit UI, invoice queue, email preview pane, and the audit log.

**Slide 9: Sample Output Comparison**
- Include a screenshot or text of a "Stage 1" (Warm) email side-by-side with a "Stage 4" (Stern) email to visually demonstrate the LLM's tone variation.

**Slide 10: Learnings & Conclusion**
- Value of structured JSON outputs in LLMs for reliability.
- Combining deterministic logic (escalation rules) with generative AI (email writing) produces the most reliable business agents.
- **Future improvements:** Integrating real SMTP with human-in-the-loop review before final dispatch.
