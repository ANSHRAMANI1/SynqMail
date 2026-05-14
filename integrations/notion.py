"""Notion database integration — create a page entry per email."""

import os

from notion_client import Client


def send_to_notion(email_msg, classification: dict, tag: str, dry_run: bool = False) -> bool:
    """
    Create a Notion database entry for the classified email.
    Returns True on success.
    """
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not database_id:
        return False

    action_items = classification.get("action_items", [])
    actions_text = "\n".join(f"• {a}" for a in action_items) if action_items else "None"

    if dry_run:
        print(
            f"[DRY RUN] Would create Notion entry:\n"
            f"  Subject: {email_msg.subject}\n"
            f"  Category: {classification.get('category')}\n"
            f"  Summary: {classification.get('summary')}"
        )
        return True

    notion = Client(auth=api_key)

    notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {
                "title": [{"text": {"content": email_msg.subject or "(no subject)"}}]
            },
            "From": {
                "rich_text": [{"text": {"content": email_msg.sender}}]
            },
            "Date": {
                "rich_text": [{"text": {"content": email_msg.date}}]
            },
            "Category": {
                "select": {"name": tag or classification.get("category", "other").replace("_", " ").title()}
            },
            "Urgency": {
                "select": {"name": classification.get("urgency", "medium").title()}
            },
            "Sentiment": {
                "select": {"name": classification.get("sentiment", "neutral").title()}
            },
            "Summary": {
                "rich_text": [{"text": {"content": classification.get("summary", "")}}]
            },
            "Action Items": {
                "rich_text": [{"text": {"content": actions_text}}]
            },
        },
    )

    return True
