"""
Bluestock Mutual Fund Analytics
Bonus B1 - Scheduled ETL

Workflow:
1. Download latest NAV data
2. Clean NAV history
3. Validate AMFI codes
4. Rebuild SQLite star schema
5. Validate database

Windows-safe UTF-8 subprocess handling is included.
"""

from pathlib import Path
import subprocess
import sys
import os
from datetime import datetime


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SCRIPTS_DIR = BASE_DIR / "scripts"
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "scheduled_etl.log"


# ============================================================
# LOGGING
# ============================================================

def log(message: str) -> None:
    """
    Write message to both console and UTF-8 log file.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    line = f"[{timestamp}] {message}"

    print(line)

    with LOG_FILE.open(
        "a",
        encoding="utf-8"
    ) as file:

        file.write(line + "\n")


# ============================================================
# RUN SCRIPT
# ============================================================

def run_script(script_name: str) -> None:
    """
    Run one ETL script safely using the current Python interpreter.
    """

    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():

        raise FileNotFoundError(
            f"Script not found: {script_path}"
        )

    log("=" * 70)
    log(f"START: {script_name}")
    log("=" * 70)

    # --------------------------------------------------------
    # Force UTF-8 for child Python process
    # --------------------------------------------------------

    env = os.environ.copy()

    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    # --------------------------------------------------------
    # Execute script
    # --------------------------------------------------------

    result = subprocess.run(
        [
            sys.executable,
            str(script_path)
        ],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )

    # --------------------------------------------------------
    # Capture STDOUT
    # --------------------------------------------------------

    if result.stdout:

        output = result.stdout.strip()

        if output:

            log(output)

    # --------------------------------------------------------
    # Handle failure
    # --------------------------------------------------------

    if result.returncode != 0:

        if result.stderr:

            error_output = result.stderr.strip()

            if error_output:

                log(
                    "ERROR OUTPUT:\n"
                    + error_output
                )

        raise RuntimeError(
            f"{script_name} failed "
            f"with exit code {result.returncode}"
        )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    log("=" * 70)
    log(f"SUCCESS: {script_name}")
    log("=" * 70)


# ============================================================
# MAIN ETL WORKFLOW
# ============================================================

def main() -> None:

    start_time = datetime.now()

    log("=" * 70)
    log("SCHEDULED BLUESTOCK ETL STARTED")
    log("=" * 70)

    log(
        f"Project Directory: {BASE_DIR}"
    )

    log(
        f"Python: {sys.executable}"
    )

    try:

        # ----------------------------------------------------
        # STEP 1
        # Download latest NAV data
        # ----------------------------------------------------

        run_script(
            "download_nav_fetch.py"
        )

        # ----------------------------------------------------
        # STEP 2
        # Clean NAV history
        # ----------------------------------------------------

        run_script(
            "clean_nav_history.py"
        )

        # ----------------------------------------------------
        # STEP 3
        # Validate AMFI codes
        # ----------------------------------------------------

        run_script(
            "amfi_validation.py"
        )

        # ----------------------------------------------------
        # STEP 4
        # Rebuild SQLite star schema
        # ----------------------------------------------------

        run_script(
            "load_star_schema.py"
        )

        # ----------------------------------------------------
        # STEP 5
        # Validate star schema
        # ----------------------------------------------------

        run_script(
            "validate_star_schema.py"
        )

        # ----------------------------------------------------
        # COMPLETED
        # ----------------------------------------------------

        end_time = datetime.now()

        duration = end_time - start_time

        log("=" * 70)
        log("SCHEDULED ETL COMPLETED SUCCESSFULLY")
        log(f"Duration: {duration}")
        log("=" * 70)

    except Exception as exc:

        end_time = datetime.now()

        duration = end_time - start_time

        log("=" * 70)
        log("SCHEDULED ETL FAILED")
        log(f"Duration: {duration}")
        log(f"ERROR: {exc}")
        log("=" * 70)

        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()