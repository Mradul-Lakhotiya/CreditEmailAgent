import json
import re
import time
import google.generativeai as genai

from .config import GEMINI_API_KEY, GEMINI_MODEL
from .models import Invoice, EmailDraft
from .escalation import STAGE_CONFIG

genai.configure(api_key=GEMINI_API_KEY)

_SYSTEM_PROMPT = """You are a professional Finance Collections Assistant for a B2B company in India.
Your task is to generate personalised, professional payment reminder emails based on structured invoice data.

STRICT RULES:
1. Use ONLY the data provided. Never invent figures, names, or dates.
2. Match the tone EXACTLY to the stage description given.
3. Output ONLY a valid JSON object with exactly three keys: "subject", "body", "tone_used".
4. Every field must be populated — no placeholders, no lorem ipsum.
5. Do not include any text, markdown, or explanation outside the JSON object.
6. Keep the email concise, professional, and actionable.
7. Address the client by their first name only (e.g. "Hi Rajesh" or "Dear Mr. Sharma").
"""


def _strip_code_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) > 1:
            raw = parts[1]
        else:
            raw = parts[0]
    if raw.startswith("json"):
        raw = raw[4:]
    return raw.strip()


def _normalize_quotes(raw: str) -> str:
    return raw.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")


def _extract_json(raw: str) -> str:
    raw = _normalize_quotes(_strip_code_fence(raw))
    start = raw.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in model output:\n{raw}")

    brace_depth = 0
    in_string = False
    escape = False
    for idx, ch in enumerate(raw[start:], start=start):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0:
                return raw[start:idx + 1].strip()

    raise ValueError(f"Could not extract a complete JSON object from model output:\n{raw}")


FALLBACK_MODELS = [
    "models/gemini-flash-lite",
    "models/gemini-2.0-flash",
]


def _parse_retry_delay(exc_text: str) -> int:
    m = re.search(r"retry_delay[^0-9]*(\d+)", exc_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"retry after ~?(\d+)", exc_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 0


def _is_quota_signal(raw: str) -> bool:
    raw_lower = raw.lower()
    return (
        "quota exceeded" in raw_lower
        or "rate limit" in raw_lower
        or "429" in raw_lower
        or "generate_content_free_tier_requests" in raw_lower
    )


def _generate_with_retry(model, prompt: str, max_attempts: int = 3):
    attempt = 0
    while True:
        try:
            return model.generate_content(prompt)
        except Exception as exc:
            attempt += 1
            msg = str(exc)
            if attempt >= max_attempts or ("429" not in msg and "quota" not in msg.lower()):
                raise
            delay = _parse_retry_delay(msg) or min(2**attempt, 30)
            time.sleep(delay)


def generate_email(invoice: Invoice) -> EmailDraft:
    """Call Gemini to generate a personalised follow-up email for one invoice."""
    stage_info = STAGE_CONFIG[invoice.stage]
    first_name = invoice.client_name.split()[0]

    prompt = f"""Generate a payment reminder email using the details below.

INVOICE DETAILS:
- Invoice Number  : {invoice.invoice_no}
- Client Name     : {invoice.client_name}  (use first name: {first_name})
- Client Company  : {invoice.client_company}
- Amount Due      : ₹{invoice.amount:,.0f}
- Due Date        : {invoice.due_date.strftime('%d %B %Y')}
- Days Overdue    : {invoice.days_overdue} days
- Payment Link    : {invoice.payment_link}

TONE STAGE     : {stage_info['label']}
REQUIRED TONE  : {stage_info['tone']}
KEY MESSAGE    : {stage_info['key_message']}
CALL TO ACTION : {stage_info['cta']}

Output ONLY this JSON (no extra text):
{{
  "subject": "<email subject line>",
  "body": "<full email body with greeting, content, CTA, and sign-off>",
  "tone_used": "{stage_info['tone']}"
}}"""

    model_names = [GEMINI_MODEL] + FALLBACK_MODELS
    last_error = None

    for model_name in model_names:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=_SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0,
                max_output_tokens=512,
            ),
        )

        try:
            response = _generate_with_retry(model, prompt)
        except Exception as exc:
            last_error = exc
            continue

        raw = response.text.strip()
        if _is_quota_signal(raw):
            last_error = RuntimeError(
                f"Quota signal detected from model {model_name}: {raw}"
            )
            continue

        try:
            json_text = _extract_json(raw)
            data = json.loads(json_text)
            return EmailDraft(**data)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"Failed to generate a valid email. Tried models {model_names}. Last error: {last_error}"
    )
