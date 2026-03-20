import requests
import csv
import os
import time
from urllib.parse import urlparse
from logger import log

from config import (
    JSEARCH_URL,
    JSEARCH_HEADERS,
    JSEARCH_QUERIES,
    MAX_JOBS,
    JOBS_FILE,
    REMOTE_KEYWORDS
)

# -----------------------------
# HELPERS
# -----------------------------
def extract_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return ""


def is_remote(text):
    try:
        return any(x in text.lower() for x in REMOTE_KEYWORDS)
    except:
        return False


def safe_request(query, retries=3, delay=2):
    for attempt in range(retries):
        try:
            res = requests.get(
                JSEARCH_URL,
                headers=JSEARCH_HEADERS,
                params={"query": query, "page": "1", "num_pages": "1"},
                timeout=10
            )

            if res.status_code == 200:
                return res

            log(f"API error ({res.status_code}) → {query}", "ERROR")

        except requests.exceptions.Timeout:
            log(f"Timeout ({attempt+1}) → {query}", "ERROR")

        except requests.exceptions.RequestException as e:
            log(f"Request failed ({attempt+1}) → {e}", "ERROR")

        time.sleep(delay)

    return None


# -----------------------------
# FETCH JOBS
# -----------------------------
def fetch_jobs():
    collected = {}
    
    for query in JSEARCH_QUERIES:
        log(f"🔎 Fetching: {query}")

        res = safe_request(query)
        if not res:
            continue

        try:
            data = res.json()
        except ValueError:
            log("Invalid JSON response", "ERROR")
            continue

        for job in data.get("data", []):
            try:
                title = job.get("job_title") or ""
                company = job.get("employer_name") or ""
                desc = job.get("job_description") or ""

                if not title or not company:
                    continue

                if not is_remote(title + desc):
                    continue

                domain = extract_domain(job.get("employer_website") or "")

                # 🔴 KEY FILTER (IMPORTANT)
                if not domain:
                    continue

                job_link = job.get("job_apply_link") or ""
                if not job_link:
                    continue

                # ✅ dedupe early
                if job_link in collected:
                    continue

                collected[job_link] = {
                    "job_title": title,
                    "company": company,
                    "company_domain": domain,
                    "job_description": desc[:300],
                    "job_link": job_link,
                    "source": "JSearch"
                }

                log(f"✅ Added: {company} ({len(collected)})")

                if len(collected) >= MAX_JOBS:
                    log("🎯 MAX_JOBS reached")
                    return list(collected.values())

            except Exception as e:
                log(f"Skipping bad job → {e}", "WARNING")

    return list(collected.values())


# -----------------------------
# SAVE JOBS
# -----------------------------
def save_jobs(jobs):
    if not jobs:
        raise RuntimeError("No jobs found")

    os.makedirs(os.path.dirname(JOBS_FILE) or ".", exist_ok=True)

    with open(JOBS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
        writer.writeheader()
        writer.writerows(jobs)

    log(f"💾 Saved {len(jobs)} jobs → {JOBS_FILE}")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    try:
        jobs = fetch_jobs()

        if not jobs:
            raise RuntimeError("No jobs collected")

        save_jobs(jobs)

        log("🔥 Step1 completed")

    except Exception as e:
        log(f"❌ Step1 failed: {e}", "ERROR")
        raise