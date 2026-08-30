# Mutual Fund Data Dictionary

## Project
Mutual Fund Analysis

---

# 1. fund_master

| Column | Data Type | Business Definition | Source |
|---------|-----------|---------------------|--------|
| amfi_code | Integer | Unique AMFI scheme code | fund_master.csv |
| scheme_name | Text | Name of the mutual fund scheme | fund_master.csv |
| fund_house | Text | Asset Management Company (AMC) | fund_master.csv |
| category | Text | Fund category (Equity, Debt, etc.) | fund_master.csv |
| sub_category | Text | Detailed fund classification | fund_master.csv |
| plan | Text | Growth / IDCW plan | fund_master.csv |

---

# 2. nav_history

| Column | Data Type | Business Definition | Source |
|---------|-----------|---------------------|--------|
| amfi_code | Integer | Unique scheme identifier | nav_history.csv |
| date | Date | NAV date | nav_history.csv |
| nav | Decimal | Net Asset Value of the scheme | nav_history.csv |

---

# 3. investor_transactions

| Column | Data Type | Business Definition | Source |
|---------|-----------|---------------------|--------|
| investor_id | Integer | Unique investor ID | investor_transactions.csv |
| transaction_date | Date | Date of transaction | investor_transactions.csv |
| amfi_code | Integer | Mutual fund scheme code | investor_transactions.csv |
| transaction_type | Text | SIP, Lumpsum, Redemption | investor_transactions.csv |
| amount_inr | Decimal | Transaction amount (₹) | investor_transactions.csv |
| state | Text | Investor state | investor_transactions.csv |
| city | Text | Investor city | investor_transactions.csv |
| payment_mode | Text | Payment method | investor_transactions.csv |
| kyc_status | Text | KYC verification status | investor_transactions.csv |

---

# 4. scheme_performance

| Column | Data Type | Business Definition | Source |
|---------|-----------|---------------------|--------|
| amfi_code | Integer | Scheme identifier | scheme_performance.csv |
| return_1yr_pct | Decimal | 1-Year Return (%) | scheme_performance.csv |
| return_3yr_pct | Decimal | 3-Year Return (%) | scheme_performance.csv |
| return_5yr_pct | Decimal | 5-Year Return (%) | scheme_performance.csv |
| benchmark_3yr_pct | Decimal | Benchmark 3-Year Return (%) | scheme_performance.csv |
| alpha | Decimal | Alpha performance metric | scheme_performance.csv |
| beta | Decimal | Beta risk metric | scheme_performance.csv |
| sharpe_ratio | Decimal | Risk-adjusted return | scheme_performance.csv |
| sortino_ratio | Decimal | Downside risk-adjusted return | scheme_performance.csv |
| std_dev_ann_pct | Decimal | Annualized standard deviation | scheme_performance.csv |
| max_drawdown_pct | Decimal | Maximum drawdown (%) | scheme_performance.csv |
| aum_crore | Decimal | Assets Under Management (Crore ₹) | scheme_performance.csv |
| expense_ratio_pct | Decimal | Expense ratio (%) | scheme_performance.csv |
| morningstar_rating | Integer | Morningstar rating | scheme_performance.csv |
| risk_grade | Text | Risk category | scheme_performance.csv |