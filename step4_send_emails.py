import csv
import smtplib
import time
import os
from email.mime.text import MIMEText
from datetime import datetime
from logger import log

from config import (
    SMTP_SERVER,
    SMTP_PORT,
    SENDER_EMAIL,
    SENDER_PASSWORD,
    MAX_EMAILS_PER_RUN,
    DELAY_BETWEEN_EMAILS,
    EMAILS_FILE,
    SENT_LOG,
    DRY_RUN,
    DELIVERY_LOG
)

# -----------------------------
# VALIDATION
# -----------------------------
def is_valid_email_payload(subject, body):
    if not subject or len(subject.strip()) < 3:
        return False
    if not body or len(body.strip()) < 20:
        return False
    return True


# -----------------------------
# CHECK SENT
# -----------------------------
def already_sent(email):
    if not os.path.exists(SENT_LOG):
        return False

    with open(SENT_LOG, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return any(row["email"] == email for row in reader)



def log_delivery(email, subject, status, error=""):

    file_exists = os.path.exists(DELIVERY_LOG)

    with open(DELIVERY_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["email", "subject", "status", "error", "timestamp"]
        )

        # write header only once
        if not file_exists or os.stat(DELIVERY_LOG).st_size == 0:
            writer.writeheader()

        writer.writerow({
            "email": email,
            "subject": subject,
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
# -----------------------------
# LOG SENT
# -----------------------------
def log_sent(email):

    file_exists = os.path.exists(SENT_LOG)

    with open(SENT_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["email", "timestamp"]
        )

        if not file_exists or os.stat(SENT_LOG).st_size == 0:
            writer.writeheader()

        writer.writerow({
            "email": email,
            "timestamp": datetime.now().isoformat()
        })

# -----------------------------
# SEND EMAIL
# -----------------------------
def send_email(server, to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        server.send_message(msg)
        log(f"✅ Sent → {to_email}")
        log_delivery(to_email, subject, "SENT")
        return True

    except Exception as e:
        error_msg = str(e)
        log(f"❌ Failed → {to_email} | {error_msg}", "ERROR")
        log_delivery(to_email, subject, "FAILED", error_msg)
        return False


# -----------------------------
# MAIN
# -----------------------------
def process():

    if not os.path.exists(EMAILS_FILE):
        log(f"❌ File not found: {EMAILS_FILE}", "ERROR")
        return

    count = 0

    if DRY_RUN:
        log(f"[DRY] {email}")
        log_delivery(email, subject, "DRY_RUN")
        success = True

    try:
        with open(EMAILS_FILE, newline='', encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
    except Exception as e:
        log(f"❌ Failed to read file: {e}", "ERROR")
        return

    # SMTP connection (safe)
    server = None

    if not DRY_RUN:
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            log("🔐 SMTP connected")
        except Exception as e:
            log(f"❌ SMTP error: {e}", "ERROR")
            return

    try:
        for row in reader:

            if count >= MAX_EMAILS_PER_RUN:
                log("🎯 Max email limit reached")
                break

            email = row.get("email", "").strip()
            subject = row.get("subject", "").strip()
            body = row.get("body", "").strip()

            if not email:
                continue

            if already_sent(email):
                log(f"⏭️ Skipping (already sent): {email}")
                continue

            if not is_valid_email_payload(subject, body):
                log(f"⚠️ Invalid email content → {email}")
                continue

            log(f"\n📤 Sending → {email}")

            if DRY_RUN:
                log(f"[DRY] Subject: {subject}")
                log(f"[DRY] Body: {body[:120]}...")
                success = True
            else:
                success = send_email(server, email, subject, body)

            if success:
                log_sent(email)
                count += 1

                # delay ONLY on real send
                if not DRY_RUN:
                    time.sleep(DELAY_BETWEEN_EMAILS)

    except Exception as e:
        log(f"❌ Runtime error: {e}", "ERROR")

    finally:
        if server:
            server.quit()
            log("🔌 SMTP disconnected")

    log(f"\n✅ Finished → {count} emails sent")
    

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    process()