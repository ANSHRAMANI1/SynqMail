# SynqMail — Intelligent Email Workflow Automation Platform

> Automatically read, classify, summarize, and route incoming emails using GPT-4o — then send them to Slack or Notion without lifting a finger.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green) ![Slack](https://img.shields.io/badge/Integrations-Slack%20%7C%20Notion-purple) ![License](https://img.shields.io/badge/License-MIT-yellow)

## The Problem

Support teams and operations managers receive hundreds of emails daily. Manually triaging, summarizing, and forwarding emails to the right person or tool costs hours every week. SynqMail automates this entirely — read once, classified and routed automatically.

**What it does in 3 steps:**
1. Connects to your Gmail/IMAP inbox and reads unread emails
2. GPT-4o classifies each email (support request, billing, spam, sales lead, etc.) and generates a summary
3. Routes the email to the right destination: Slack channel, Notion database, or a CSV report

## Features

- Connects to any IMAP mailbox (Gmail, Outlook, custom)
- AI-powered classification into configurable categories
- One-line summaries and action items extracted per email
- Route to Slack (channel webhooks) and/or Notion (database entries)
- Fallback to local CSV log if no integrations configured
- Configurable rules per category (e.g. "billing → #billing-alerts")
- Dry-run mode to preview what would happen without sending anything
- Runs as a scheduled job (cron) or one-shot script

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| LLM | OpenAI GPT-4o |
| Email | imaplib (built-in) + email (built-in) |
| Slack | Slack Incoming Webhooks |
| Notion | Notion API (official) |
| Scheduling | APScheduler |
| Config | YAML + .env |

## Project Structure

```
SynqMail/
├── main.py                     # Entrypoint — run once or start scheduler
├── processors/
│   ├── __init__.py
│   ├── email_reader.py         # IMAP connection and email fetching
│   └── ai_classifier.py        # GPT-4o classification and summarization
├── integrations/
│   ├── __init__.py
│   ├── slack.py                # Slack webhook sender
│   └── notion.py               # Notion database entry creator
├── config/
│   └── routing_rules.yaml      # Category → destination routing config
├── requirements.txt
├── .env.example
└── README.md
```

## Quickstart

### 1. Clone and install

```bash
git clone [Contact me on Upwork](https://www.upwork.com/freelancers/~0169dbb8a7f7cf38e6) [https://github.com/ANSHRAMANI1/SynqMail.git](https://github.com/ANSHRAMANI1/SynqMail.git)
cd SynqMail
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Fill in OPENAI_API_KEY, IMAP credentials, and integration tokens
```

### 3. Edit routing rules

Edit `config/routing_rules.yaml` to define what happens to each email category.

### 4. Run

```bash
# Process inbox once
python main.py --run-once

# Start the scheduler (default: every 15 minutes)
python main.py --schedule

# Dry run — preview without sending anything
python main.py --run-once --dry-run
```

## How It Works

```
IMAP Inbox → Fetch Unread Emails
                   ↓
          GPT-4o Classification
          (category + summary + action items)
                   ↓
         Routing Rules (routing_rules.yaml)
          ↙              ↓              ↘
    Slack Channel    Notion DB      Local CSV Log
```

## Configuration

### .env keys

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `IMAP_HOST` | IMAP server (e.g. imap.gmail.com) |
| `IMAP_USER` | Email address |
| `IMAP_PASSWORD` | App password (not your main password) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `NOTION_API_KEY` | Notion integration token |
| `NOTION_DATABASE_ID` | Target Notion database ID |
| `CHECK_INTERVAL_MINUTES` | How often to poll (default: 15) |

### Gmail Setup

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) instead of your main password. Enable IMAP in Gmail settings.

### routing_rules.yaml

```yaml
categories:
  support_request:
    destinations: [slack]
    slack_channel: "#support-triage"
  billing_issue:
    destinations: [slack, notion]
    slack_channel: "#billing-alerts"
  sales_lead:
    destinations: [notion]
  spam:
    destinations: []  # discard
```

## Email Categories (Default)

GPT-4o classifies each email into one of:

- `support_request` — Customer needs help
- `billing_issue` — Invoice or payment related
- `sales_lead` — Potential new business
- `job_application` — Hiring related
- `newsletter` — Marketing / subscription emails
- `internal` — From your own domain
- `spam` — Junk
- `other` — Anything else

Categories are fully customizable via the routing rules config.

## Use Cases

- **SaaS support teams** — Auto-triage incoming tickets to Slack
- **Freelancers** — Never miss a lead, route inquiries to Notion CRM
- **Operations teams** — Log and categorize all vendor/partner emails
- **E-commerce** — Separate order issues from general queries

## Freelance Context

This was built as a portfolio project demonstrating end-to-end AI automation. I build custom versions for clients with their specific email categories, integrations (HubSpot, Salesforce, Monday.com, etc.), and deployment needs.

**Want this for your team?** [Contact me on Upwork](https://www.upwork.com/freelancers/~0169dbb8a7f7cf38e6)

## License

MIT
