"""
Bluestock Mutual Fund Analytics
Live NAV Data Downloader

Purpose:
    Download historical NAV data from MFAPI for selected
    Direct Plan - Growth mutual fund schemes.

Important:
    - AMFI code must match the API response.
    - API scheme name must match the expected scheme.
    - Wrong/mismatched API responses are NEVER saved.
    - Old/incorrect CSV files are removed only after successful
      validation and replacement.

Project:
    D:\mutual-fund-analysis
"""

from pathlib import Path
import sys
import time
import requests
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"

FUND_MASTER_FILE = RAW_DIR / "fund_master.csv"


# ============================================================
# MFAPI SETTINGS
# ============================================================

API_BASE_URL = "https://api.mfapi.in/mf"

MAX_RETRIES = 5

RETRY_DELAY_SECONDS = 7

REQUEST_TIMEOUT = 90


# ============================================================
# FUNDS
# ============================================================
#
# IMPORTANT:
# These codes MUST correspond to the codes currently present
# in your fund_master.csv.
#
# The script also validates the API response before saving.
#
# ============================================================

FUNDS = {

    "HDFC_Top100_Direct": {
        "amfi_code": 125497,

        "expected_keywords": [
            "hdfc",
            "top",
            "100",
            "direct",
            "growth",
        ],
    },

    "SBI_Large_Cap_Direct": {
        "amfi_code": 119598,

        "expected_keywords": [
            "sbi",
            "large",
            "cap",
            "direct",
            "growth",
        ],
    },

    "ICICI_Large_Cap_Direct": {
        "amfi_code": 120586,

        "expected_keywords": [
            "icici",
            "prudential",
            "large",
            "cap",
            "direct",
            "growth",
        ],
    },

    "Nippon_Large_Cap_Direct": {
        "amfi_code": 118633,

        "expected_keywords": [
            "nippon",
            "india",
            "large",
            "cap",
            "direct",
            "growth",
        ],
    },

    "Axis_Large_Cap_Direct": {
        "amfi_code": 120465,

        "expected_keywords": [
            "axis",
            "large",
            "cap",
            "direct",
            "growth",
        ],
    },
}


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Connection": "keep-alive",
    }
)


# ============================================================
# PRINT HELPER
# ============================================================

def print_line(char="=", length=70):
    print(char * length)


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(value):
    """
    Normalize text for comparison.

    Example:

        HDFC Top 100 Fund - Direct Plan - Growth

    becomes:

        hdfctop100funddirectplangrowth
    """

    if value is None:
        return ""

    text = str(value).lower()

    for char in [
        " ",
        "-",
        "_",
        ".",
        "/",
        "&",
        ",",
        "(",
        ")",
        ":",
    ]:
        text = text.replace(char, "")

    return text


# ============================================================
# VERIFY SCHEME NAME
# ============================================================

def verify_scheme_name(
    returned_name,
    expected_keywords
):
    """
    Verify that the returned API scheme contains
    all required keywords.

    This is more reliable than splitting the filename
    using underscores.
    """

    normalized_name = normalize_text(
        returned_name
    )

    missing_keywords = []

    for keyword in expected_keywords:

        normalized_keyword = normalize_text(
            keyword
        )

        if (
            normalized_keyword
            not in normalized_name
        ):

            missing_keywords.append(
                keyword
            )

    if missing_keywords:

        return False, missing_keywords

    return True, []


# ============================================================
# LOAD FUND MASTER
# ============================================================

def load_fund_master():

    if not FUND_MASTER_FILE.exists():

        raise FileNotFoundError(
            f"Fund master file not found:\n"
            f"{FUND_MASTER_FILE}"
        )

    df = pd.read_csv(
        FUND_MASTER_FILE
    )

    required_columns = {
        "amfi_code",
        "scheme_name",
        "fund_house",
        "category",
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "fund_master.csv is missing columns: "
            f"{sorted(missing_columns)}"
        )

    df["amfi_code"] = pd.to_numeric(
        df["amfi_code"],
        errors="coerce"
    )

    return df


# ============================================================
# FIND MASTER RECORD
# ============================================================

def find_master_record(
    fund_master,
    amfi_code
):
    """
    Find AMFI code in fund_master.csv.

    Returns a single row or None.
    """

    matches = fund_master[
        fund_master["amfi_code"]
        == int(amfi_code)
    ]

    if matches.empty:

        return None

    return matches.iloc[0]


# ============================================================
# REQUEST NAV DATA
# ============================================================

def request_nav_data(amfi_code):

    url = (
        f"{API_BASE_URL}/"
        f"{amfi_code}"
    )

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        print(
            f"Attempt     : "
            f"{attempt}/{MAX_RETRIES}"
        )

        try:

            response = SESSION.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            status_code = (
                response.status_code
            )

            # ------------------------------------------------
            # SERVER ERROR
            # ------------------------------------------------

            if status_code >= 500:

                raise requests.HTTPError(
                    f"Server error "
                    f"{status_code}: "
                    f"{response.reason}"
                )

            # ------------------------------------------------
            # OTHER HTTP ERRORS
            # ------------------------------------------------

            response.raise_for_status()

            # ------------------------------------------------
            # JSON PARSE
            # ------------------------------------------------

            try:

                data = response.json()

            except ValueError as error:

                raise ValueError(
                    "MFAPI returned invalid JSON."
                ) from error

            if not isinstance(
                data,
                dict
            ):

                raise ValueError(
                    "Unexpected MFAPI response format."
                )

            return data

        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.HTTPError,
        ) as error:

            last_error = error

            print(
                f"ERROR: {error}"
            )

            if attempt < MAX_RETRIES:

                print(
                    f"Retrying in "
                    f"{RETRY_DELAY_SECONDS} seconds..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

        except Exception as error:

            last_error = error

            print(
                f"ERROR: {error}"
            )

            break

    raise RuntimeError(
        "API request failed after "
        f"{MAX_RETRIES} attempts.\n"
        f"AMFI Code: {amfi_code}\n"
        f"Last Error: {last_error}"
    )


# ============================================================
# PROCESS NAV DATA
# ============================================================

def process_nav_data(
    data,
    fund_name,
    amfi_code,
    expected_keywords
):

    # --------------------------------------------------------
    # BASIC RESPONSE VALIDATION
    # --------------------------------------------------------

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            "Unexpected MFAPI response format."
        )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    meta = data.get(
        "meta",
        {}
    )

    if not isinstance(
        meta,
        dict
    ):

        raise ValueError(
            "MFAPI metadata is invalid."
        )

    returned_code = meta.get(
        "scheme_code"
    )

    returned_name = meta.get(
        "scheme_name",
        ""
    )

    # --------------------------------------------------------
    # VERIFY AMFI CODE
    # --------------------------------------------------------

    try:

        returned_code = int(
            returned_code
        )

    except (
        TypeError,
        ValueError,
    ):

        raise ValueError(
            "MFAPI response does not contain "
            "a valid scheme_code."
        )

    if returned_code != int(
        amfi_code
    ):

        raise ValueError(
            "\n"
            "==================================================\n"
            "AMFI CODE MISMATCH\n"
            "==================================================\n"
            f"Fund       : {fund_name}\n"
            f"Requested  : {amfi_code}\n"
            f"Returned   : {returned_code}\n"
            f"API Scheme : {returned_name}\n"
            "=================================================="
        )

    # --------------------------------------------------------
    # VERIFY SCHEME NAME
    # --------------------------------------------------------

    name_valid, missing_keywords = (
        verify_scheme_name(
            returned_name,
            expected_keywords
        )
    )

    if not name_valid:

        raise ValueError(
            "\n"
            "==================================================\n"
            "WRONG SCHEME RETURNED BY MFAPI\n"
            "==================================================\n"
            f"Fund       : {fund_name}\n"
            f"AMFI Code  : {amfi_code}\n"
            f"API Scheme : {returned_name}\n"
            f"Missing    : {missing_keywords}\n"
            "==================================================\n"
            "DATA WAS NOT SAVED.\n"
            "=================================================="
        )

    # --------------------------------------------------------
    # VERIFY DIRECT PLAN
    # --------------------------------------------------------

    returned_lower = (
        returned_name.lower()
    )

    if "direct" not in returned_lower:

        raise ValueError(
            "\n"
            "MFAPI returned a NON-DIRECT scheme.\n"
            f"AMFI Code : {amfi_code}\n"
            f"Scheme    : {returned_name}\n"
            "DATA WAS NOT SAVED."
        )

    # --------------------------------------------------------
    # VERIFY GROWTH
    # --------------------------------------------------------

    if "growth" not in returned_lower:

        raise ValueError(
            "\n"
            "MFAPI returned a scheme that is "
            "NOT a Growth option.\n"
            f"AMFI Code : {amfi_code}\n"
            f"Scheme    : {returned_name}\n"
            "DATA WAS NOT SAVED."
        )

    # --------------------------------------------------------
    # NAV RECORDS
    # --------------------------------------------------------

    records = data.get(
        "data"
    )

    if records is None:

        raise ValueError(
            "MFAPI response does not contain NAV data."
        )

    if not isinstance(
        records,
        list
    ):

        raise ValueError(
            "MFAPI NAV data is not a list."
        )

    if len(records) == 0:

        raise ValueError(
            "MFAPI returned an empty NAV dataset."
        )

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    df = pd.DataFrame(
        records
    )

    required_columns = {
        "date",
        "nav",
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "NAV response missing columns: "
            f"{sorted(missing_columns)}"
        )

    original_rows = len(
        df
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    # --------------------------------------------------------
    # NAV
    # --------------------------------------------------------

    df["nav"] = pd.to_numeric(
        df["nav"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # INVALID ROWS
    # --------------------------------------------------------

    invalid_mask = (
        df["date"].isna()
        |
        df["nav"].isna()
        |
        (df["nav"] <= 0)
    )

    invalid_rows = int(
        invalid_mask.sum()
    )

    df = df[
        ~invalid_mask
    ].copy()

    if df.empty:

        raise ValueError(
            "No valid NAV records remain "
            "after cleaning."
        )

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    before_duplicates = len(
        df
    )

    df = df.drop_duplicates(
        subset=["date"]
    )

    duplicate_rows = (
        before_duplicates
        - len(df)
    )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    df = (
        df.sort_values("date")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # AMFI CODE
    # --------------------------------------------------------

    df["amfi_code"] = int(
        amfi_code
    )

    # --------------------------------------------------------
    # FINAL COLUMNS
    # --------------------------------------------------------

    df = df[
        [
            "amfi_code",
            "date",
            "nav",
        ]
    ]

    return (
        df,
        original_rows,
        invalid_rows,
        duplicate_rows,
        returned_name,
    )


# ============================================================
# SAVE NAV FILE
# ============================================================

def save_nav_file(
    df,
    file_path
):

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Temporary file first.
    # This prevents a partial CSV from becoming the
    # official dataset if saving is interrupted.

    temp_file = file_path.with_suffix(
        ".tmp"
    )

    df.to_csv(
        temp_file,
        index=False,
        encoding="utf-8"
    )

    # Replace old file only after successful write.

    temp_file.replace(
        file_path
    )


# ============================================================
# DOWNLOAD ONE FUND
# ============================================================

def download_fund(
    fund_name,
    config,
    fund_master
):

    amfi_code = int(
        config["amfi_code"]
    )

    expected_keywords = (
        config["expected_keywords"]
    )

    print_line()

    print(
        f"Downloading : {fund_name}"
    )

    print(
        f"AMFI Code   : {amfi_code}"
    )

    print_line()

    # --------------------------------------------------------
    # FUND MASTER CHECK
    # --------------------------------------------------------

    master_record = (
        find_master_record(
            fund_master,
            amfi_code
        )
    )

    if master_record is None:

        print(
            "WARNING: AMFI code is not present "
            "in fund_master.csv."
        )

        print(
            "API validation will still be performed."
        )

    else:

        master_scheme = str(
            master_record["scheme_name"]
        )

        print(
            f"Master Scheme: "
            f"{master_scheme}"
        )

    # --------------------------------------------------------
    # REQUEST API
    # --------------------------------------------------------

    try:

        data = request_nav_data(
            amfi_code
        )

    except Exception as error:

        print(
            f"FAILED: Could not download "
            f"{fund_name}"
        )

        print(
            f"ERROR: {error}"
        )

        return False

    # --------------------------------------------------------
    # PROCESS AND VALIDATE
    # --------------------------------------------------------

    try:

        (
            df,
            original_rows,
            invalid_rows,
            duplicate_rows,
            api_scheme_name,
        ) = process_nav_data(
            data,
            fund_name,
            amfi_code,
            expected_keywords
        )

    except Exception as error:

        print(
            "FAILED: NAV validation failed."
        )

        print(
            f"ERROR: {error}"
        )

        return False

    # --------------------------------------------------------
    # API SCHEME
    # --------------------------------------------------------

    print(
        f"API Scheme   : "
        f"{api_scheme_name}"
    )

    # --------------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------------

    output_file = (
        RAW_DIR
        /
        f"{fund_name}.csv"
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    try:

        save_nav_file(
            df,
            output_file
        )

    except Exception as error:

        print(
            "FAILED: Could not save CSV."
        )

        print(
            f"ERROR: {error}"
        )

        return False

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    first_date = (
        df["date"]
        .min()
        .date()
    )

    last_date = (
        df["date"]
        .max()
        .date()
    )

    latest_nav = float(
        df.sort_values(
            "date"
        )
        .iloc[-1]["nav"]
    )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    print(
        f"Saved Successfully : "
        f"{output_file}"
    )

    print(
        f"Rows Downloaded    : "
        f"{len(df):,}"
    )

    print(
        f"Invalid Rows Removed: "
        f"{invalid_rows:,}"
    )

    print(
        f"Duplicate Rows Removed: "
        f"{duplicate_rows:,}"
    )

    print(
        f"Date Range         : "
        f"{first_date} to {last_date}"
    )

    print(
        f"Latest NAV         : "
        f"{latest_nav}"
    )

    print(
        "Status             : SUCCESS"
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print_line()

    print(
        "BLUESTOCK MUTUAL FUND NAV DOWNLOAD"
    )

    print_line()

    print(
        f"Project Directory : "
        f"{BASE_DIR}"
    )

    print(
        f"Output Directory  : "
        f"{RAW_DIR}"
    )

    print(
        f"Funds to Download : "
        f"{len(FUNDS)}"
    )

    print_line()

    # --------------------------------------------------------
    # CREATE DIRECTORY
    # --------------------------------------------------------

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # LOAD FUND MASTER
    # --------------------------------------------------------

    try:

        fund_master = (
            load_fund_master()
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

        return 1

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    successful_funds = []

    failed_funds = []

    for fund_name, config in FUNDS.items():

        success = download_fund(
            fund_name,
            config,
            fund_master
        )

        if success:

            successful_funds.append(
                fund_name
            )

        else:

            failed_funds.append(
                fund_name
            )

        # Small delay between requests.

        time.sleep(2)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()

    print_line()

    print(
        "NAV DOWNLOAD SUMMARY"
    )

    print_line()

    print(
        f"Successful Downloads : "
        f"{len(successful_funds)}/"
        f"{len(FUNDS)}"
    )

    print(
        f"Failed Downloads     : "
        f"{len(failed_funds)}/"
        f"{len(FUNDS)}"
    )

    # --------------------------------------------------------
    # SUCCESSFUL
    # --------------------------------------------------------

    if successful_funds:

        print()

        print(
            "SUCCESSFUL FUNDS:"
        )

        for fund in successful_funds:

            print(
                f"  PASS - {fund}"
            )

    # --------------------------------------------------------
    # FAILED
    # --------------------------------------------------------

    if failed_funds:

        print()

        print(
            "FAILED FUNDS:"
        )

        for fund in failed_funds:

            print(
                f"  FAIL - {fund}"
            )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print()

    print(
        f"Raw NAV Directory: "
        f"{RAW_DIR}"
    )

    print_line()

    # --------------------------------------------------------
    # EXIT CODE
    # --------------------------------------------------------

    if failed_funds:

        print(
            "NAV DOWNLOAD COMPLETED WITH ERRORS."
        )

        print_line()

        return 1

    print(
        "NAV DOWNLOAD COMPLETED SUCCESSFULLY."
    )

    print_line()

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        exit_code = main()

        sys.exit(
            exit_code
        )

    except KeyboardInterrupt:

        print()

        print(
            "NAV download interrupted by user."
        )

        sys.exit(130)

    except Exception as error:

        print()

        print_line()

        print(
            "UNEXPECTED ERROR"
        )

        print_line()

        print(
            f"ERROR: {error}"
        )

        print_line()

        sys.exit(1)