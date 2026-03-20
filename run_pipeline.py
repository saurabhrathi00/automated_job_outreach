import subprocess
import os
import shutil
from datetime import datetime
from logger import log

from config import (
    JOBS_FILE,
    LEADS_FILE,
    EMAILS_FILE,
    ARCHIVE_FOLDER,
    TEMP_FOLDER,
    RUN_STEP_1,
    RUN_STEP_2,
    RUN_STEP_3,
    RUN_STEP_4
)

# -----------------------------
# RUN STEP (WITH RETRY)
# -----------------------------
def run_step(script_name, expected_file, retries=2):
    log(f"🚀 Running {script_name}")

    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["python3", script_name],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                log(result.stdout.strip())

            if result.stderr:
                log(result.stderr.strip(), "ERROR")

            if result.returncode == 0 and os.path.exists(expected_file):
                log(f"✅ {script_name} completed")
                return True

            log(f"⚠️ Attempt {attempt+1} failed for {script_name}", "WARNING")

        except subprocess.TimeoutExpired:
            log(f"❌ Timeout in {script_name}", "ERROR")

        except Exception as e:
            log(f"❌ Error running {script_name}: {e}", "ERROR")

    log(f"❌ {script_name} failed after retries", "ERROR")
    return False


# -----------------------------
# ARCHIVE + CLEANUP
# -----------------------------
def archive_and_cleanup():
    if not os.path.exists(EMAILS_FILE):
        log("⚠️ No final file to archive")
        return

    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    final_path = os.path.join(ARCHIVE_FOLDER, f"emails_{timestamp}.csv")

    try:
        shutil.move(EMAILS_FILE, final_path)
        log(f"📦 Final saved: {final_path}")
    except Exception as e:
        log(f"❌ Failed to archive final file: {e}", "ERROR")
        return

    # move intermediate files
    for f in [JOBS_FILE, LEADS_FILE]:
        if os.path.exists(f):
            try:
                new_path = os.path.join(
                    TEMP_FOLDER,
                    f"{f.replace('.csv', '')}_{timestamp}.csv"
                )
                shutil.move(f, new_path)
                log(f"📁 Moved {f} → {new_path}")
            except Exception as e:
                log(f"⚠️ Failed moving {f}: {e}", "WARNING")

    log("🧼 Cleanup done")


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def main():

    success = True

    if RUN_STEP_1:
        if not run_step("step1_fetch_jobs.py", JOBS_FILE):
            log("❌ Step1 failed → stopping pipeline", "ERROR")
            return

    if RUN_STEP_2:
        if not run_step("step2_generate_leads.py", LEADS_FILE):
            log("⚠️ Step2 failed → continuing", "WARNING")
            success = False

    if RUN_STEP_3:
        if not run_step("step3_generate_emails.py", EMAILS_FILE):
            log("⚠️ Step3 failed → continuing", "WARNING")
            success = False

    if RUN_STEP_4:
        if not run_step("step4_send_emails.py", EMAILS_FILE):
            log("⚠️ Step4 failed → continuing", "WARNING")
            success = False

    archive_and_cleanup()

    if success:
        log("🔥 PIPELINE COMPLETED SUCCESSFULLY")
    else:
        log("⚠️ PIPELINE COMPLETED WITH ERRORS", "WARNING")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    main()