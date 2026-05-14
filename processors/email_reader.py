"""IMAP email reader — connects to an inbox and fetches unread messages."""

import email
import imaplib
import os
from dataclasses import dataclass, field
from email.header import decode_header
from email.utils import parsedate_to_datetime


@dataclass
class EmailMessage:
    uid: str
    subject: str
    sender: str
    date: str
    body: str
    raw_headers: dict = field(default_factory=dict)


def _decode_header_value(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _extract_body(msg: email.message.Message) -> str:
    """Walk a MIME message and return the plain-text body."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in disposition:
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
    else:
        charset = msg.get_content_charset() or "utf-8"
        return msg.get_payload(decode=True).decode(charset, errors="replace")
    return ""


def fetch_unread_emails(max_count: int = 0) -> list[EmailMessage]:
    """
    Connect to the configured IMAP server and return unread emails.
    Marks fetched emails as seen.
    Set max_count=0 for no limit.
    """
    host = os.environ["IMAP_HOST"]
    port = int(os.getenv("IMAP_PORT", 993))
    user = os.environ["IMAP_USER"]
    password = os.environ["IMAP_PASSWORD"]
    mailbox = os.getenv("IMAP_MAILBOX", "INBOX")

    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(user, password)
    conn.select(mailbox)

    _, data = conn.search(None, "UNSEEN")
    uids = data[0].split()

    if max_count and max_count > 0:
        uids = uids[:max_count]

    messages = []
    for uid in uids:
        _, msg_data = conn.fetch(uid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subject = _decode_header_value(msg.get("Subject", "(no subject)"))
        sender = _decode_header_value(msg.get("From", ""))
        date_raw = msg.get("Date", "")
        try:
            date = parsedate_to_datetime(date_raw).isoformat()
        except Exception:
            date = date_raw

        body = _extract_body(msg)

        messages.append(EmailMessage(
            uid=uid.decode(),
            subject=subject,
            sender=sender,
            date=date,
            body=body[:4000],  # cap body length sent to GPT
        ))

        # Mark as seen
        conn.store(uid, "+FLAGS", "\\Seen")

    conn.logout()
    return messages
