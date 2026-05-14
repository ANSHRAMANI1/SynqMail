"""GPT-4o email classification and summarization."""

import json
import os

from openai import OpenAI

from processors.email_reader import EmailMessage

VALID_CATEGORIES = [
    "support_request",
    "billing_issue",
    "sales_lead",
    "job_application",
    "newsletter",
    "internal",
    "spam",
    "other",
]

SYSTEM_PROMPT = """You are an email classification assistant. Given an email, return a JSON object with:
- "category": one of the following exactly: support_request, billing_issue, sales_lead, job_application, newsletter, internal, spam, other
- "summary": a single sentence (max 20 words) describing what the email is about
- "action_items": a list of strings (max 3) — concrete next steps, or empty list if none needed
- "urgency": one of "high", "medium", "low"
- "sentiment": one of "positive", "neutral", "negative"

Respond with ONLY valid JSON. No explanation, no markdown.
"""


def classify_email(email_msg: EmailMessage) -> dict:
    """
    Classify and summarize a single email using GPT-4o.
    Returns a dict with keys: category, summary, action_items, urgency, sentiment.
    """
    client = OpenAI()

    user_content = f"""From: {email_msg.sender}
Subject: {email_msg.subject}
Date: {email_msg.date}

Body:
{email_msg.body}
"""

    response = client.chat.completions.create(
        model=os.getenv("MODEL_NAME", "gpt-4o"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    # Validate category — fall back to "other" if unexpected value returned
    if result.get("category") not in VALID_CATEGORIES:
        result["category"] = "other"

    # Ensure required keys exist
    result.setdefault("summary", "(no summary)")
    result.setdefault("action_items", [])
    result.setdefault("urgency", "medium")
    result.setdefault("sentiment", "neutral")

    return result


def classify_batch(emails: list[EmailMessage]) -> list[dict]:
    """Classify a list of emails, returning enriched result dicts."""
    results = []
    for email_msg in emails:
        try:
            classification = classify_email(email_msg)
        except Exception as e:
            classification = {
                "category": "other",
                "summary": f"Classification failed: {e}",
                "action_items": [],
                "urgency": "low",
                "sentiment": "neutral",
            }

        results.append({
            "email": email_msg,
            "classification": classification,
        })

    return results
