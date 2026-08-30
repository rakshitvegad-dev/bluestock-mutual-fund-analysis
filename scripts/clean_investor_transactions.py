import pandas as pd

# Load dataset
df = pd.read_csv(r"D:\mutual-fund-analysis\data\raw\investor_transactions.csv")

print("Original Shape:", df.shape)
print("\nColumns:")
print(df.columns)

# -----------------------------
# Convert transaction date
# -----------------------------
df["transaction_date"] = pd.to_datetime(
    df["transaction_date"],
    errors="coerce"
)

# -----------------------------
# Standardize transaction_type
# -----------------------------
df["transaction_type"] = (
    df["transaction_type"]
      .str.strip()
      .str.title()
)

replace_dict = {
    "Sip": "SIP",
    "Lump Sum": "Lumpsum",
    "Lumpsum": "Lumpsum",
    "Redeem": "Redemption",
    "Redemption": "Redemption"
}

df["transaction_type"] = df["transaction_type"].replace(replace_dict)

# -----------------------------
# Remove invalid amounts
# -----------------------------
df["amount_inr"] = pd.to_numeric(
    df["amount_inr"],
    errors="coerce"
)

# -----------------------------
# Standardize KYC status
# -----------------------------
df["kyc_status"] = (
    df["kyc_status"]
      .astype(str)
      .str.strip()
      .str.title()
)

valid_status = [
    "Verified",
    "Pending",
    "Rejected"
]

df["kyc_status"] = df["kyc_status"].where(
    df["kyc_status"].isin(valid_status),
    "Unknown"
)

# -----------------------------
# Remove duplicates
# -----------------------------
df = df.drop_duplicates()

print("\nCleaned Shape:", df.shape)

# Save
df.to_csv(
    "data/processed/investor_transactions_cleaned.csv",
    index=False
)

print("\nInvestor transactions cleaned successfully!")