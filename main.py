"""SynqMail — AI Email Automation Pipeline — entrypoint."""

import argparse
import csv
import logging
import os
from datetime import datetime
from pathlib import Path

import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from integrations.notion import send_to_notion
from integrations.slack import send_to_slack
from processors.ai_classifier import classify_batch
from processors.email_reader import fetch_unread_emails

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

RULES_PATH = Path(__file__).parent / "config" / "routing_rules.yaml"
CSV_LOG_PATH = Path("email_log.csv")


def load_routing_rules() -> dict:
    with open(RULES_PATH) as f:
        return yaml.safe_load(f).get("categories", {})


def append_to_csv(email_msg, classification: dict) -> None:
    write_header = not CSV_LOG_PATH.exists()
    with open(CSV_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "uid", "from", "subject", "date",
            "category", "urgency", "sentiment", "summary", "action_items",
        ])
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(),
            "uid": email_msg.uid,
            "from": email_msg.sender,
            "subject": email_msg.subject,
            "date": email_msg.date,
            "category": classification.get("category"),
            "urgency": classification.get("urgency"),
            "sentiment": classification.get("sentiment"),
            "summary": classification.get("summary"),
            "action_items": " | ".join(classification.get("action_items", [])),
        })


def process_inbox(dry_run: bool = False) -> None:
    log.info("Starting inbox processing run...")

    max_emails = int(os.getenv("MAX_EMAILS_PER_RUN", 50))
    emails = fetch_unread_emails(max_count=max_emails)
    log.info(f"Fetched {len(emails)} unread email(s)")

    if not emails:
        log.info("No unread emails. Done.")
        return

    rules = load_routing_rules()
    results = classify_batch(emails)

    sent_slack = sent_notion = logged_csv = 0

    for item in results:
        email_msg = item["email"]
        clf = item["classification"]
        category = clf["category"]
        rule = rules.get(category, {})
        destinations = rule.get("destinations", [])

        log.info(
            f"  [{category.upper()}] {email_msg.subject[:60]!r} | "
            f"{clf['urgency']} urgency | {clf['sentiment']} | "
            f"→ {destinations or 'discarded'}"
        )

        if "slack" in destinations:
            channel_label = rule.get("slack_channel", "#general")
            ok = send_to_slack(email_msg, clf, channel_label, dry_run=dry_run)
            if ok:
                sent_slack += 1

        if "notion" in destinations:
            tag = rule.get("notion_tag", category)
            ok = send_to_notion(email_msg, clf, tag, dry_run=dry_run)
            if ok:
                sent_notion += 1

        if "csv" in destinations or not destinations:
            append_to_csv(email_msg, clf)
            logged_csv += 1

    log.info(
        f"Run complete — Slack: {sent_slack}, Notion: {sent_notion}, CSV: {logged_csv} "
        f"{'[DRY RUN]' if dry_run else ''}"
    )


def main():
    parser = argparse.ArgumentParser(description="SynqMail — AI Email Automation Pipeline")
    parser.add_argument("--run-once", action="store_true", help="Process inbox once and exit")
    parser.add_argument("--schedule", action="store_true", help="Start the scheduler")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without sending")
    args = parser.parse_args()

    if args.dry_run:
        log.info("DRY RUN mode enabled — no messages will be sent")

    if args.run_once or (not args.schedule):
        process_inbox(dry_run=args.dry_run)
        return

    interval = int(os.getenv("CHECK_INTERVAL_MINUTES", 15))
    log.info(f"Starting scheduler — checking every {interval} minutes")

    scheduler = BlockingScheduler()
    scheduler.add_job(
        process_inbox,
        "interval",
        minutes=interval,
        kwargs={"dry_run": args.dry_run},
        next_run_time=datetime.now(),  # run immediately on start
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
