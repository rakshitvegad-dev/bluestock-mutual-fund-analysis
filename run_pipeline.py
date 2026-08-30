"""
Bluestock Mutual Fund Analytics - Master Pipeline

Runs the reproducible core ETL and database validation workflow.

Usage:
    python run_pipeline.py

Interactive analytics such as the fund recommender can be executed
separately using scripts/recommender.py.
"""

from pathlib import Path
import subprocess
import sys
import time


BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"


PIPELINE_STEPS = [
    ("Data ingestion", "data_ingestion.py"),
    ("NAV history cleaning", "clean_nav_history.py"),
    ("Investor transaction cleaning", "clean_investor_transactions.py"),
    ("AMFI validation", "amfi_validation.py"),
    ("Star schema loading", "load_star_schema.py"),
    ("Star schema validation", "validate_star_schema.py"),
]


def run_script(step_name: str, script_name: str) -> None:
    """Execute one pipeline script and stop if it fails."""

    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(
            f"Required script not found: {script_path}"
        )

    print("\n" + "=" * 80)
    print(f"PIPELINE STEP: {step_name}")
    print(f"SCRIPT: {script_name}")
    print("=" * 80)

    start_time = time.time()

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
    )

    elapsed = time.time() - start_time

    if result.returncode != 0:
        raise RuntimeError(
            f"Pipeline stopped because {script_name} "
            f"failed with exit code {result.returncode}."
        )

    print(
        f"\nSUCCESS: {step_name} "
        f"completed in {elapsed:.2f} seconds."
    )


def main() -> None:
    """Run the complete reproducible core analytics pipeline."""

    print("=" * 80)
    print("BLUESTOCK MUTUAL FUND ANALYTICS")
    print("MASTER PIPELINE")
    print("=" * 80)
    print(f"Project directory: {BASE_DIR}")

    pipeline_start = time.time()

    try:
        for step_name, script_name in PIPELINE_STEPS:
            run_script(step_name, script_name)

        total_time = time.time() - pipeline_start

        print("\n" + "=" * 80)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"Total execution time: {total_time:.2f} seconds")
        print("Core ETL and database validation completed.")
        print("=" * 80)

    except Exception as error:
        total_time = time.time() - pipeline_start

        print("\n" + "=" * 80)
        print("PIPELINE FAILED")
        print("=" * 80)
        print(f"Error: {error}")
        print(f"Execution time: {total_time:.2f} seconds")
        print("=" * 80)

        sys.exit(1)


if __name__ == "__main__":
    main()
