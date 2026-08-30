# ============================================================
# MUTUAL FUND RECOMMENDER
# ============================================================
# Input:
#   Risk appetite -> Low / Moderate / High
#
# Output:
#   Top 3 funds by Sharpe Ratio within the selected risk grade
#
# Project structure:
#   mutual-fund-analysis/
#   ├── data/
#   │   └── processed/
#   │       ├── sharpe_ratio.csv
#   │       └── cleaned_scheme_performance.csv
#   └── scripts/
#       └── recommender.py
# ============================================================


import os
import pandas as pd


# ============================================================
# 1. PROJECT ROOT
# ============================================================

# __file__ =
# D:\mutual-fund-analysis\scripts\recommender.py
#
# First dirname -> scripts
# Second dirname -> mutual-fund-analysis

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# 2. DATA PATHS
# ============================================================

SHARPE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "sharpe_ratio.csv"
)

PERFORMANCE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "cleaned_scheme_performance.csv"
)


# ============================================================
# 3. CHECK FILES
# ============================================================

if not os.path.exists(SHARPE_PATH):
    raise FileNotFoundError(
        f"Sharpe file not found:\n{SHARPE_PATH}"
    )

if not os.path.exists(PERFORMANCE_PATH):
    raise FileNotFoundError(
        f"Performance file not found:\n{PERFORMANCE_PATH}"
    )


# ============================================================
# 4. LOAD DATA
# ============================================================

sharpe = pd.read_csv(
    SHARPE_PATH
)

performance = pd.read_csv(
    PERFORMANCE_PATH
)


print("=" * 65)
print("MUTUAL FUND RECOMMENDER - DATA LOADING")
print("=" * 65)

print(
    f"\nSharpe data loaded: {sharpe.shape}"
)

print(
    f"Performance data loaded: {performance.shape}"
)


# ============================================================
# 5. VALIDATE REQUIRED COLUMNS
# ============================================================

required_sharpe_columns = [
    "amfi_code",
    "scheme_name",
    "Sharpe_Ratio",
    "Sharpe_Rank"
]

required_performance_columns = [
    "amfi_code",
    "risk_grade"
]


missing_sharpe = [
    col
    for col in required_sharpe_columns
    if col not in sharpe.columns
]

missing_performance = [
    col
    for col in required_performance_columns
    if col not in performance.columns
]


if missing_sharpe:
    raise KeyError(
        "Missing columns in sharpe_ratio.csv: "
        + str(missing_sharpe)
    )


if missing_performance:
    raise KeyError(
        "Missing columns in cleaned_scheme_performance.csv: "
        + str(missing_performance)
    )


# ============================================================
# 6. CLEAN AMFI CODES
# ============================================================

sharpe["amfi_code"] = (
    sharpe["amfi_code"]
    .astype(str)
    .str.strip()
)

performance["amfi_code"] = (
    performance["amfi_code"]
    .astype(str)
    .str.strip()
)


# ============================================================
# 7. PREPARE RISK DATA
# ============================================================

risk_data = performance[
    [
        "amfi_code",
        "risk_grade"
    ]
].copy()


risk_data["risk_grade"] = (
    risk_data["risk_grade"]
    .astype(str)
    .str.strip()
    .str.title()
)


# ============================================================
# 8. REMOVE DUPLICATE RISK RECORDS
# ============================================================

risk_data = (
    risk_data
    .drop_duplicates(
        subset=["amfi_code"]
    )
)


# ============================================================
# 9. MERGE SHARPE + RISK GRADE
# ============================================================

recommender_data = sharpe.merge(
    risk_data,
    on="amfi_code",
    how="left"
)


# ============================================================
# 10. CLEAN SHARPE RATIO
# ============================================================

recommender_data["Sharpe_Ratio"] = pd.to_numeric(
    recommender_data["Sharpe_Ratio"],
    errors="coerce"
)


# ============================================================
# 11. REMOVE INVALID RECORDS
# ============================================================

recommender_data = recommender_data[
    recommender_data["Sharpe_Ratio"].notna()
].copy()


# ============================================================
# 12. DISPLAY DATASET VALIDATION
# ============================================================

print(
    "\nRecommender dataset:",
    recommender_data.shape
)

print(
    "\nRisk grades available:"
)

print(
    recommender_data["risk_grade"]
    .value_counts(dropna=False)
)


missing_risk = (
    recommender_data["risk_grade"]
    .isna()
    .sum()
)

print(
    f"\nMissing risk grades: {missing_risk}"
)


# ============================================================
# 13. RECOMMENDATION FUNCTION
# ============================================================

def recommend_funds(
    risk_appetite,
    top_n=3
):
    """
    Return top funds by Sharpe Ratio
    for the selected risk appetite.

    Parameters
    ----------
    risk_appetite : str
        Low, Moderate, or High

    top_n : int
        Number of funds to recommend

    Returns
    -------
    pandas.DataFrame
    """

    # --------------------------------------------------------
    # Standardize user input
    # --------------------------------------------------------

    risk_appetite = (
        str(risk_appetite)
        .strip()
        .title()
    )


    # --------------------------------------------------------
    # Valid risk levels
    # --------------------------------------------------------

    valid_risk_levels = [
        "Low",
        "Moderate",
        "High"
    ]


    if risk_appetite not in valid_risk_levels:

        raise ValueError(
            "Invalid risk appetite. "
            "Please choose Low, Moderate, or High."
        )


    # --------------------------------------------------------
    # Filter matching funds
    # --------------------------------------------------------

    matching_funds = recommender_data[
        recommender_data["risk_grade"]
        == risk_appetite
    ].copy()


    # --------------------------------------------------------
    # Check availability
    # --------------------------------------------------------

    if matching_funds.empty:

        return pd.DataFrame(
            columns=[
                "Recommendation_Rank",
                "amfi_code",
                "scheme_name",
                "risk_grade",
                "Sharpe_Ratio",
                "Sharpe_Rank"
            ]
        )


    # --------------------------------------------------------
    # Sort by Sharpe Ratio
    # Highest Sharpe = better risk-adjusted performance
    # --------------------------------------------------------

    recommendations = (
        matching_funds
        .sort_values(
            "Sharpe_Ratio",
            ascending=False
        )
        .head(top_n)
        .copy()
    )


    # --------------------------------------------------------
    # Add recommendation rank
    # --------------------------------------------------------

    recommendations[
        "Recommendation_Rank"
    ] = range(
        1,
        len(recommendations) + 1
    )


    # --------------------------------------------------------
    # Select output columns
    # --------------------------------------------------------

    recommendations = recommendations[
        [
            "Recommendation_Rank",
            "amfi_code",
            "scheme_name",
            "risk_grade",
            "Sharpe_Ratio",
            "Sharpe_Rank"
        ]
    ]


    return recommendations


# ============================================================
# 14. SAVE RECOMMENDER DATASET
# ============================================================

RECOMMENDER_OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "fund_recommender_data.csv"
)


recommender_data.to_csv(
    RECOMMENDER_OUTPUT_PATH,
    index=False
)


print(
    "\n✅ Recommender dataset saved:"
)

print(
    RECOMMENDER_OUTPUT_PATH
)


# ============================================================
# 15. TEST ALL THREE RISK LEVELS
# ============================================================

print("\n")
print("=" * 65)
print("RECOMMENDER VALIDATION")
print("=" * 65)


for risk_level in [
    "Low",
    "Moderate",
    "High"
]:

    print(
        f"\n{'-' * 65}"
    )

    print(
        f"Top 3 Funds — {risk_level} Risk"
    )

    print(
        f"{'-' * 65}"
    )


    result = recommend_funds(
        risk_level,
        top_n=3
    )


    if result.empty:

        print(
            f"⚠️ No funds found for {risk_level} risk."
        )

    else:

        print(
            result.to_string(
                index=False
            )
        )


# ============================================================
# 16. INTERACTIVE USER INPUT
# ============================================================

print("\n")
print("=" * 65)
print("INTERACTIVE FUND RECOMMENDER")
print("=" * 65)

print(
    "\nAvailable risk appetites:"
)

print("1. Low")
print("2. Moderate")
print("3. High")


user_input = input(
    "\nEnter your risk appetite: "
)


try:

    result = recommend_funds(
        user_input,
        top_n=3
    )


    if result.empty:

        print(
            "\n⚠️ No matching funds found."
        )

    else:

        print("\n")
        print("=" * 65)

        print(
            f"TOP 3 RECOMMENDED FUNDS — "
            f"{str(user_input).strip().title()} RISK"
        )

        print("=" * 65)

        print(
            result.to_string(
                index=False
            )
        )


except ValueError as error:

    print(
        f"\n❌ Error: {error}"
    )


# ============================================================
# END
# ============================================================