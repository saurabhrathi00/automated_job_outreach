import csv
import requests
from serpapi import GoogleSearch
from logger import log

from config import (
    SERP_API_KEY,
    SEARCH_QUERY_TEMPLATE,
    TOP_N_CANDIDATES,
    TEST_MODE,
    OPENAI_API_KEY,
    HUNTER_API_KEY,
    EMAIL_PATTERN,
    HUNTER_CONFIDENCE_THRESHOLD,
    USE_FALLBACK_EMAIL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    CANDIDATE_SELECTION_PROMPT,
    JOBS_FILE,
    LEADS_FILE
)

# -----------------------------
# SEARCH LINKEDIN
# -----------------------------
def search_linkedin(company):
    query = SEARCH_QUERY_TEMPLATE.format(company=company)

    try:
        data = GoogleSearch({
            "engine": "google",
            "q": query,
            "api_key": SERP_API_KEY,
            "num": 10
        }).get_dict()
    except Exception as e:
        log(f"SerpAPI error: {e}", "ERROR")
        return []

    candidates = []

    for r in data.get("organic_results", []):
        title = r.get("title", "")
        link = r.get("link", "")

        if "linkedin.com/in" not in link:
            continue

        if "-" not in title:
            continue

        t = title.lower()

        # remove irrelevant roles
        if any(x in t for x in ["ceo", "founder", "vp", "director", "hr", "recruiter"]):
            continue

        # allow partial fuzzy match
        if company.lower()[:6] not in t:
            continue

        candidates.append(title)

    log(f"Candidates: {candidates}")
    return candidates[:TOP_N_CANDIDATES]


# -----------------------------
# FALLBACK SEARCH
# -----------------------------
def fallback_search(company):
    log("⚠️ Using fallback search")

    query = f'site:linkedin.com/in "{company}" engineer'

    try:
        data = GoogleSearch({
            "engine": "google",
            "q": query,
            "api_key": SERP_API_KEY,
            "num": 5
        }).get_dict()

        return [
            r.get("title", "")
            for r in data.get("organic_results", [])
            if "linkedin.com/in" in r.get("link", "")
        ]

    except Exception:
        return []


# -----------------------------
# EXTRACT NAME
# -----------------------------
def extract_name(text):
    return text.split("-")[0].strip()


# -----------------------------
# EMAIL GENERATION (fallback)
# -----------------------------
def generate_email(name, domain):
    parts = name.lower().split()
    if len(parts) < 2 or not domain:
        return None

    return EMAIL_PATTERN.format(
        first=parts[0],
        last=parts[-1],
        domain=domain
    )


# -----------------------------
# HUNTER
# -----------------------------
def find_email_with_hunter(name, domain):
    if not domain:
        return None

    try:
        res = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": domain,
                "full_name": name,
                "api_key": HUNTER_API_KEY
            },
            timeout=10
        )

        data = res.json().get("data", {})
        email = data.get("email")
        confidence = data.get("confidence", 0)

        log(f"Hunter → {email} ({confidence})")

        if email and confidence >= HUNTER_CONFIDENCE_THRESHOLD:
            return email

        if email:
            log("⚠️ Low confidence email")

        return email

    except Exception as e:
        log(f"Hunter error: {e}", "ERROR")
        return None


# -----------------------------
# LLM PICK
# -----------------------------
def pick_best_candidate(candidates):
    if TEST_MODE:
        return extract_name(candidates[0])

    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM_MODEL,
                "messages": [{
                    "role": "user",
                    "content": CANDIDATE_SELECTION_PROMPT.format(candidates=candidates)
                }],
                "temperature": LLM_TEMPERATURE
            },
            timeout=15
        )

        data = res.json()

        if "choices" not in data:
            log(f"OpenAI error: {data}", "ERROR")
            return extract_name(candidates[0])

        return extract_name(data["choices"][0]["message"]["content"])

    except Exception as e:
        log(f"LLM error: {e}", "ERROR")
        return extract_name(candidates[0])


# -----------------------------
# MAIN
# -----------------------------
def process_jobs():
    results = {}
    
    with open(JOBS_FILE, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for job in reader:
            company = job["company"]
            domain = job["company_domain"]

            log(f"\nProcessing: {company}")

            candidates = search_linkedin(company)

            if not candidates:
                candidates = fallback_search(company)

            if not candidates:
                log("❌ No candidates")
                continue

            best = pick_best_candidate(candidates)
            log(f"Selected: {best}")

            email = None

            if not TEST_MODE:
                email = find_email_with_hunter(best, domain)

            if not email and USE_FALLBACK_EMAIL:
                email = generate_email(best, domain)
                log(f"Fallback email: {email}")

            if not email:
                continue

            # dedupe by email
            if email in results:
                continue

            results[email] = {
                "company": company,
                "job_title": job["job_title"],
                "person": best,
                "email": email,
                "email_text": ""
            }

    if not results:
        log("❌ No leads generated", "ERROR")
        return

    with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results.values())[0].keys())
        writer.writeheader()
        writer.writerows(results.values())

    log(f"✅ Saved {len(results)} leads → {LEADS_FILE}")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    process_jobs()