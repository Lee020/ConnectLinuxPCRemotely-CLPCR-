##### add "EMAIL_ACCOUNT" and "PASSWORD"

import imaplib
import email
from email.header import decode_header
import time
import subprocess
import os

# Configuration
IMAP_SERVER = 'imap.gmail.com'
EMAIL_ACCOUNT = 'example2.com'
PASSWORD = 'vcdvbcxcvdsd'  # Use app password if 2FA is enabled
MAILBOX = 'INBOX'
CHECK_INTERVAL = 10  # seconds
TRIGGER_KEYWORD = "trigger"
SCRIPT_PATH = "/home/path/ttyd-ngrok-gmail.sh"

# Track processed UIDs
seen_uids = set()

def decode_mime_words(s):
    """Decode encoded email headers (e.g., Subject)"""
    if not s:
        return ""
    decoded = decode_header(s)
    return ''.join(
        part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
        for part, enc in decoded
    )

def extract_body(msg):
    """Get plain text body from email"""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                return part.get_payload(decode=True).decode(errors='ignore').strip()
    else:
        if msg.get_content_type() == "text/plain":
            return msg.get_payload(decode=True).decode(errors='ignore').strip()
    return ""

def run_script_if_triggered(body):
    """Check for trigger and run shell script"""
    if TRIGGER_KEYWORD.lower() in body.lower():
        print(f"🚀 Trigger word '{TRIGGER_KEYWORD}' found. Running script...")
        try:
            result = subprocess.run(
                [SCRIPT_PATH],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("✅ Script output:\n", result.stdout)
        except subprocess.CalledProcessError as e:
            print("❌ Script failed with error:\n", e.stderr)
    else:
        print("⏭️ No trigger word found in email.")

def read_email(msg):
    """Parse and act on email content"""
    subject = decode_mime_words(msg['Subject'] or 'No Subject')
    from_ = decode_mime_words(msg['From'] or 'Unknown')

    print(f"\n📩 New Email Received!")
    print(f"From: {from_}")
    print(f"Subject: {subject}")

    body = extract_body(msg)
    print("Body:\n", body)
    run_script_if_triggered(body)

def listen_for_mail():
    print("🔁 Listening for new emails...\n")
    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_ACCOUNT, PASSWORD)
            mail.select(MAILBOX)

            result, data = mail.uid('search', None, 'UNSEEN')
            if result == 'OK':
                uids = data[0].split()
                new_uids = [uid for uid in uids if uid not in seen_uids]

                for uid in new_uids:
                    res, msg_data = mail.uid('fetch', uid, '(RFC822)')
                    if res == 'OK':
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        read_email(msg)
                        seen_uids.add(uid)

            mail.logout()
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n👋 Stopped by user.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    listen_for_mail()
