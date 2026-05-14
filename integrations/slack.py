"""Slack incoming webhook integration."""

import os

import requests

URGENCY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
SENTIMENT_EMOJI = {"positive": "😊", "neutral": "😐", "negative": "😟"}


def send_to_slack(email_msg, classification: dict, channel_label: str, dry_run: bool = False) -> bool:
    """
    Send a formatted email summary to a Slack channel via incoming webhook.
    Returns True on success.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False

    urgency = classification.get("urgency", "medium")
    sentiment = classification.get("sentiment", "neutral")
    category = classification.get("category", "other").replace("_", " ").title()
    summary = classification.get("summary", "")
    action_items = classification.get("action_items", [])

    actions_text = ""
    if action_items:
        actions_text = "\n*Action Items:*\n" + "\n".join(f"• {a}" for a in action_items)

    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{URGENCY_EMOJI.get(urgency, '⚪')} New Email: {category}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*From:*\n{email_msg.sender}"},
                    {"type": "mrkdwn", "text": f"*Subject:*\n{email_msg.subject}"},
                    {"type": "mrkdwn", "text": f"*Date:*\n{email_msg.date}"},
                    {"type": "mrkdwn", "text": f"*Routed to:*\n{channel_label}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Summary:* {summary}"
                        f"\n*Urgency:* {urgency.title()}  |  "
                        f"*Sentiment:* {SENTIMENT_EMOJI.get(sentiment, '')} {sentiment.title()}"
                        f"{actions_text}"
                    ),
                },
            },
            {"type": "divider"},
        ]
    }

    if dry_run:
        print(f"[DRY RUN] Would send to Slack:\n  From: {email_msg.sender}\n  Summary: {summary}")
        return True

    response = requests.post(webhook_url, json=message, timeout=10)
    return response.status_code == 200
