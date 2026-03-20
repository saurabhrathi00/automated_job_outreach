# 🚀 Automated Job Outreach Pipeline

An end-to-end automation system that:

1. Fetches remote software jobs
2. Finds relevant engineers/managers
3. Generates personalized cold emails using LLM
4. Sends emails via SMTP
5. Tracks delivery status and logs results

---

# 📌 Features

* 🔍 Job scraping (JSearch API)
* 👤 Lead discovery (LinkedIn via SerpAPI)
* 📧 Email generation (OpenAI)
* 📤 Email sending (SMTP - Zoho/Gmail)
* 📊 Logging (sent + delivery tracking)
* 🔁 Retry-ready architecture
* 🧹 Auto cleanup + archiving

---

# 🏗️ Project Structure

```
.
├── step1_fetch_jobs.py        # Fetch jobs → jobs.csv
├── step2_generate_leads.py    # Find people + emails → leads_with_emails.csv
├── step3_generate_emails.py   # Generate emails → emails_ready.csv
├── step4_send_emails.py       # Send emails
├── run_pipeline.py            # Orchestrates full flow
├── config.py                  # All configuration
├── logger.py                  # Logging utility
├── requirements.txt
│
├── output/                    # Final results
├── temp/                      # Intermediate archived files
│
├── jobs.csv
├── leads_with_emails.csv
├── emails_ready.csv
├── sent_log.csv
├── delivery_log.csv
```

---

# ⚙️ Setup

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 2. Create `.env`

```
OPENAI_API_KEY=your_key
HUNTER_API_KEY=your_key
SERP_API_KEY=your_key
JSEARCH_API_KEY=your_key

SENDER_EMAIL=your_email
SENDER_PASSWORD=your_password

SMTP_SERVER=smtp.zoho.in
SMTP_PORT=587
RESUME_LINK=
```

---

## 3. Configure `config.py`

Important flags:

```python
DRY_RUN = True        # SAFE MODE (no emails sent)
RUN_STEP_4 = False    # disable sending initially
MAX_EMAILS_PER_RUN = 1
DELAY_BETWEEN_EMAILS = 60
```

---

# ▶️ How It Works

### Step 1 → Fetch Jobs

* Uses JSearch API
* Filters remote roles

### Step 2 → Generate Leads

* Finds LinkedIn profiles via Google (SerpAPI)
* Extracts candidate names
* Finds emails via Hunter (or fallback)

### Step 3 → Generate Emails

* Uses LLM to write short cold emails
* Includes resume link (optional)

### Step 4 → Send Emails

* Sends via SMTP
* Logs success/failure

---

# 🧪 Run Pipeline

```bash
python3 run_pipeline.py
```

---

# 📊 Output Files

## `emails_ready.csv`

Contains:

* recipient email
* subject
* body

---

## `sent_log.csv`

Tracks:

```csv
email,timestamp
```

---

## `delivery_log.csv`

Tracks:

```csv
email,subject,status,error,timestamp
```

Statuses:

* `SENT`
* `FAILED`
* `DRY_RUN`

---

# 🔐 Safety Guidelines (IMPORTANT)

* Always start with:

```python
DRY_RUN = True
```

* Then switch:

```python
DRY_RUN = False
MAX_EMAILS_PER_RUN = 1
```

* Gradually scale

---

# ⚠️ Known Limitations

* Hunter confidence can be low (emails may be wrong)
* No open/reply tracking yet
* Some LinkedIn results may be irrelevant
* JSearch API may timeout occasionally

---

# 🚀 Future Improvements

* Bounce detection (IMAP)
* Retry failed emails
* Email open tracking
* Better candidate ranking (remove LLM dependency)
* Domain-based email validation
* Multi-account sending (scale safely)

---

# 💣 Reality Check

This system:

* ✔ automates outreach
* ✔ sends emails
* ✔ logs activity

But success depends on:

* 🎯 targeting quality
* ✉️ email copy
* 📬 deliverability

---

# 👤 Author

Saurabh Rathi

---

# 📬 Usage Philosophy

> Don’t spam.
> Send fewer, better emails.
> Optimize for replies, not volume.
