import csv
import requests
import time
from logger import log

from config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    LEADS_FILE,
    EMAILS_FILE,
    EMAIL_GENERATION_PROMPT,
    SENDER_NAME,
    RESUME_LINK,
    INCLUDE_RESUME_LINK
)

# -----------------------------
# PARSE RESPONSE (ROBUST)
# -----------------------------
def parse_response(text):
    subject = "Quick question"
    body = "Hi, reaching out regarding this role."

    try:
        lines = text.strip().split("\n")

        for line in lines:
            if line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()

        if "Body:" in text:
            body = text.split("Body:", 1)[1].strip()
        else:
            body = text.strip()

    except Exception as e:
        log(f"Parsing failed: {e}", "ERROR")

    return subject, body


# -----------------------------
# VALIDATE OUTPUT
# -----------------------------
def validate_email(subject, body):
    if not subject or len(subject) < 3:
        return False
    if not body or len(body) < 20:
        return False
    return True


# -----------------------------
# LLM CALL
# -----------------------------
def generate_email(person, company, job_title):

    prompt = EMAIL_GENERATION_PROMPT.format(
        sender_name=SENDER_NAME,
        person=person,
        company=company,
        job_title=job_title,
        resume_link=RESUME_LINK if INCLUDE_RESUME_LINK else ""
    )

    for attempt in range(3):
        try:
            res = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.6
                },
                timeout=15
            )

            if res.status_code != 200:
                log(f"OpenAI error: {res.text}", "ERROR")
                time.sleep(2 * (attempt + 1))
                continue

            data = res.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not text:
                log("Empty LLM response")
                continue

            subject, body = parse_response(text)

            if validate_email(subject, body):
                return subject, body

            log("⚠️ Invalid email format → retrying")

        except Exception as e:
            log(f"LLM error (attempt {attempt+1}): {e}", "ERROR")

        time.sleep(2 * (attempt + 1))  # backoff

    return "Quick question", "Hi, reaching out regarding this role."


# -----------------------------
# MAIN
# -----------------------------
def process():
    results = {}
    
    try:
        with open(LEADS_FILE, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                email = row.get("email", "").strip()

                if not email:
                    continue

                # dedupe emails
                if email in results:
                    continue

                company = row.get("company", "")
                log(f"✉️ Generating email for {company}")

                subject, body = generate_email(
                    row.get("person", ""),
                    company,
                    row.get("job_title", "")
                )

                # enforce short body (anti-spam)
                if len(body) > 500:
                    body = body[:500]

                results[email] = {
                    "company": company,
                    "job_title": row.get("job_title", ""),
                    "person": row.get("person", ""),
                    "email": email,
                    "subject": subject,
                    "body": body
                }

                time.sleep(1)

    except FileNotFoundError:
        log(f"File not found: {LEADS_FILE}", "ERROR")
        return

    if not results:
        log("❌ No emails generated", "ERROR")
        return

    with open(EMAILS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results.values())[0].keys())
        writer.writeheader()
        writer.writerows(results.values())

    log(f"✅ Emails saved → {EMAILS_FILE}")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    process()