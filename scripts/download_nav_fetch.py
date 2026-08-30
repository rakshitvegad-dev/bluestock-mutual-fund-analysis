"""
live_nav_fetch.py

Day 1 Task:
- Fetch historical NAV data from MFAPI
- Save raw CSV files into data/raw/

Author : Rakshit Vegad
Project: Mutual Fund Analysis Internship
"""

import os
import requests
import pandas as pd

# ============================================================
# Output Folder
# ============================================================

OUTPUT_DIR = "mutual-fund-analysis/data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Mutual Fund AMFI Codes (As provided in internship task)
# ============================================================

funds = {
    "HDFC_Top100_Direct": 125497,
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841
}

# ============================================================
# Download Function
# ============================================================

def fetch_nav(amfi_code, scheme_name):

    print("=" * 70)
    print(f"Downloading : {scheme_name}")
    print(f"AMFI Code   : {amfi_code}")

    url = f"https://api.mfapi.in/mf/{amfi_code}"

    try:

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        if "data" not in data:
            print("No NAV data found.")
            return

        df = pd.DataFrame(data["data"])

        if df.empty:
            print("Empty dataset received.")
            return

        # Convert Date
        df["date"] = pd.to_datetime(
            df["date"],
            format="%d-%m-%Y",
            errors="coerce"
        )

        # Convert NAV
        df["nav"] = pd.to_numeric(
            df["nav"],
            errors="coerce"
        )

        # Remove invalid rows
        df = df.dropna()

        # Sort by date
        df = df.sort_values("date")

        # Add AMFI Code
        df["amfi_code"] = amfi_code

        # Reorder columns
        df = df[
            [
                "amfi_code",
                "date",
                "nav"
            ]
        ]

        file_path = os.path.join(
            OUTPUT_DIR,
            f"{scheme_name}.csv"
        )

        df.to_csv(file_path, index=False)

        print(f"Saved Successfully : {file_path}")
        print(f"Rows Downloaded    : {len(df)}")

    except Exception as e:
        print("Error :", e)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print("\nStarting NAV Download...\n")

    for scheme, code in funds.items():
        fetch_nav(code, scheme)

    print("\nAll NAV files downloaded successfully.")