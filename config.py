# -----------------------------
# LOAD ENV VARIABLES
# -----------------------------
import os
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# API KEYS
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY")

# -----------------------------
# PIPELINE CONTROL
# -----------------------------
TEST_MODE = False
DRY_RUN = False   # keep TRUE until tested

RUN_STEP_1 = True
RUN_STEP_2 = True
RUN_STEP_3 = True
RUN_STEP_4 = True

# -----------------------------
# FILE PATHS
# -----------------------------
JOBS_FILE = "jobs.csv"
LEADS_FILE = "leads_with_emails.csv"
EMAILS_FILE = "emails_ready.csv"

ARCHIVE_FOLDER = "output"
TEMP_FOLDER = "temp"
SENT_LOG = "sent_log.csv"

# -----------------------------
# JSEARCH CONFIG
# -----------------------------
JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"

JSEARCH_HEADERS = {
    "X-RapidAPI-Key": JSEARCH_API_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

JSEARCH_QUERIES = [
    "backend engineer remote USA",
    "frontend engineer react remote USA",
    "full stack developer remote USA",
    "python developer remote USA",
    "java developer remote USA",
    "devops engineer remote USA",
]

MAX_JOBS = 5
REMOTE_KEYWORDS = ["remote", "work from home", "distributed"]

# -----------------------------
# LINKEDIN SEARCH (SERP)
# -----------------------------
SEARCH_QUERY_TEMPLATE = (
    'site:linkedin.com/in "{company}" '
    '("software engineer" OR "engineering manager" OR "backend engineer" OR "tech lead")'
)

TOP_N_CANDIDATES = 5

# -----------------------------
# EMAIL DISCOVERY
# -----------------------------
EMAIL_PATTERN = "{first}.{last}@{domain}"
USE_FALLBACK_EMAIL = True
HUNTER_CONFIDENCE_THRESHOLD = 50

# -----------------------------
# LLM CONFIG
# -----------------------------
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.2
CANDIDATE_SELECTION_PROMPT = """
Select the BEST person to contact for a SOFTWARE ENGINEERING job.

Candidates:
{candidates}

Rules:
- Prefer: Engineering Manager, Tech Lead, Senior Engineer
- Avoid: CEO, VP, Director, HR, Recruiter

Return ONLY the NAME.
"""

EMAIL_GENERATION_PROMPT = """
Write a short cold email for a software engineer reaching out.

Details:
- Sender: {sender_name}
- Recipient: {person}
- Company: {company}
- Role: {job_title}
- Resume: {resume_link}

Rules:
- Under 100 words
- Ask ONE question
- No begging
- Sound natural

End with:
– {sender_name}

Return:
Subject: ...
Body: ...
"""

# -----------------------------
# SENDER
# -----------------------------
SENDER_NAME = "Saurabh Rathi"

# -----------------------------
# RESUME
# -----------------------------
RESUME_LINK = os.getenv("RESUME_LINK", "")
INCLUDE_RESUME_LINK = True

# -----------------------------
# SMTP CONFIG
# -----------------------------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.zoho.in")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

MAX_EMAILS_PER_RUN = 1
DELAY_BETWEEN_EMAILS = 60
DELIVERY_LOG = "delivery_log.csv"


# -----------------------------
# VALIDATION
# -----------------------------
def validate_config():
    required = [
        OPENAI_API_KEY,
        SERP_API_KEY,
        SENDER_EMAIL,
        SENDER_PASSWORD
    ]

    missing = [k for k in required if not k]

    if missing:
        raise ValueError("❌ Missing required environment variables")

validate_config()