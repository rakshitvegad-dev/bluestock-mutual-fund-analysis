import pandas as pd

fund_master = pd.read_csv(r"D:\mutual-fund-analysis\data\raw\fund_master.csv")
nav_history = pd.read_csv(r"D:\mutual-fund-analysis\data\raw\nav_history.csv")

# Check if every AMFI code exists
missing_codes = set(fund_master["amfi_code"]) - set(nav_history["amfi_code"])

print("=" * 60)
print("AMFI Code Validation")
print("=" * 60)

if len(missing_codes) == 0:
    print("✅ All AMFI codes in fund_master exist in nav_history.")
else:
    print(f"❌ Missing {len(missing_codes)} AMFI codes:")
    print(sorted(missing_codes))