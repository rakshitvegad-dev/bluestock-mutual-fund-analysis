# 📊 Mutual Fund Analytics & Investment Scorecard

## 📌 Project Overview

This project is an end-to-end **Mutual Fund Analytics and Investment Scorecard platform** designed to analyze mutual fund performance, risk, benchmark alignment, investor behavior, SIP trends, and overall investment quality.

The project combines:

* Data ingestion and ETL
* Data cleaning and validation
* Exploratory Data Analysis
* Financial performance analytics
* Risk analytics
* Benchmark analysis
* Advanced analytics
* Investor behavior analysis
* Fund recommendation
* Power BI dashboarding
* SQL analytics
* Python-based automation and reporting

The analysis focuses on approximately **40 mutual fund schemes** across multiple Indian Asset Management Companies (AMCs), along with historical NAV, investor transaction, SIP, AUM, and benchmark data.

---

# 🎯 Project Objectives

The major objectives of this project are:

* Analyze historical mutual fund NAV data.
* Clean and validate financial datasets.
* Calculate mutual fund performance metrics.
* Measure fund risk and volatility.
* Compare funds against NIFTY50 and NIFTY100 benchmarks.
* Calculate Alpha, Beta, Sharpe Ratio and Sortino Ratio.
* Calculate Maximum Drawdown.
* Calculate Tracking Error and Tracking Difference.
* Build a multi-factor Fund Scorecard.
* Rank mutual funds based on investment quality.
* Perform historical VaR and CVaR analysis.
* Analyze Rolling 90-Day Sharpe Ratio.
* Analyze investor cohorts.
* Analyze SIP continuity and investor risk.
* Build a simple risk-based fund recommender.
* Calculate sector concentration using HHI.
* Build an interactive Power BI dashboard.
* Generate business-oriented investment insights.

---

# 🗂️ Project Structure

```text
D:\mutual-fund-analysis
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── Advanced_Analytics.ipynb
│   ├── EDA_Analysis.ipynb
│   ├── Performance_Analytics.ipynb
│   ├── final_project_qa.ipynb
│   ├── python_data_analysis.ipynb
│   └── ...
│
├── scripts/
│   └── recommender.py
│
├── dashboard/
│   ├── bluestock_mf_dashboard.pbix
│   ├── Dashboard.pdf
│   ├── Page1_Industry_Overview.png
│   ├── Page2_Fund_Performance.png
│   ├── Page3_Investor_Analytics.png
│   └── Page4_SIP_Market_Trends.png
│
├── reports/
│   ├── var_cvar_report.csv
│   ├── investor_cohort_analysis.csv
│   ├── sip_continuity_analysis.csv
│   ├── fund_recommender_data.csv
│   ├── sector_hhi_analysis.csv
│   └── ...
│
├── sql/
│
├── requirements.txt
└── README.md
```

---

# 📥 Data Sources

The project uses multiple financial and investor datasets.

### Mutual Fund Data

* Fund master information
* Historical NAV data
* Scheme performance data
* AUM data
* SIP inflow data
* Investor transaction data

### Benchmark Data

Benchmark performance data includes:

* NIFTY 50
* NIFTY 100

### External API

Historical NAV information was also obtained using mutual fund APIs such as:

* AMFI India
* mfapi.in

---

# 🧹 Data Cleaning & ETL

The raw datasets were cleaned and transformed before analysis.

## NAV Data

Performed:

* Date conversion
* Sorting by fund and date
* Duplicate removal
* NAV validation
* Missing-value checks
* Daily return calculation

## Investor Transactions

Performed:

* Transaction date standardization
* Transaction type standardization
* Amount validation
* KYC status validation
* Duplicate checks
* Investor-level transaction analysis

Transaction types include:

* SIP
* Lumpsum
* Redemption

## Scheme Performance

Validated:

* Returns
* Alpha
* Beta
* Sharpe Ratio
* Sortino Ratio
* Standard deviation
* Maximum Drawdown
* Expense Ratio
* Risk Grade

---

# 🔎 Exploratory Data Analysis

EDA was performed to understand mutual fund behavior and industry trends.

### NAV Analysis

* Daily NAV trends
* Fund-level NAV movement
* Daily return distribution
* Historical performance patterns

### AUM Analysis

* AUM by fund house
* Annual AUM growth
* Fund-house comparison

### SIP Analysis

* Monthly SIP inflows
* SIP account trends
* SIP AUM
* Year-over-year SIP growth

### Investor Analysis

* Transaction behavior
* State-wise investment activity
* Age-group analysis
* City-tier analysis
* Transaction-type distribution

---

# 📈 Performance Analytics

The project calculates several key mutual fund performance metrics.

## CAGR

Compound Annual Growth Rate is used to measure annualized fund growth.

## Sharpe Ratio

Measures risk-adjusted return.

A higher Sharpe Ratio indicates better risk-adjusted performance.

## Sortino Ratio

Measures return relative to downside volatility.

## Alpha

Measures fund performance relative to its benchmark.

## Beta

Measures the sensitivity of fund returns to benchmark movements.

## Maximum Drawdown

Measures the largest historical decline from a peak to a subsequent trough.

---

# 📊 Benchmark Analysis

Funds were compared against major market benchmarks.

### Benchmarks

* NIFTY 50
* NIFTY 100

The project includes:

* Benchmark normalization
* Fund vs benchmark performance
* Tracking Error
* Tracking Difference
* Rolling 30-Day Tracking Difference

This helps identify how closely a fund follows its benchmark.

---

# 🏆 Fund Scorecard

A multi-factor **Fund Score** was developed to rank mutual funds.

The scorecard considers:

* CAGR / Return
* Sharpe Ratio
* Alpha
* Expense Ratio
* Maximum Drawdown

The scorecard contains:

```text
amfi_code
scheme_name
CAGR_3Y_pct
Return_Rank
Sharpe_Rank
Alpha_Rank
Expense_Rank
MDD_Rank
Return_Score
Sharpe_Score
Alpha_Score
Expense_Score
MDD_Score
Fund_Score
Overall_Rank
```

Funds are ranked using the final **Fund Score**.

---

# ⚠️ Advanced Risk Analytics

## Historical VaR — 95%

Historical Value at Risk was calculated using the **5th percentile of the daily return distribution**.

VaR estimates the potential loss threshold under normal historical conditions.

The analysis was performed for approximately **40 mutual fund schemes**.

Output:

```text
var_cvar_report.csv
```

## CVaR

Conditional Value at Risk was calculated as the average return of observations below the VaR threshold.

CVaR provides additional information about the severity of losses beyond the VaR level.

---

# 📉 Rolling 90-Day Sharpe Ratio

A rolling 90-day Sharpe Ratio was calculated using daily returns.

The calculation uses:

* Rolling 90-day mean return
* Rolling 90-day standard deviation
* Annualization factor √252

The analysis was visualized for selected key funds.

Output:

```text
rolling_sharpe_chart.png
```

---

# 👥 Investor Cohort Analysis

Investors were grouped according to their **first transaction year**.

For each cohort, the analysis calculates:

* Average SIP amount
* Total invested amount
* Transaction activity
* Preferred funds

Output:

```text
investor_cohort_analysis.csv
```

This analysis helps understand how investor behavior differs across entry cohorts.

---

# 🔄 SIP Continuity Analysis

Investors with **6 or more SIP transactions** were analyzed.

The analysis calculates:

* Number of SIP transactions
* Average gap between SIP transactions
* SIP continuity status

Investors with an average gap greater than **35 days** are flagged as:

```text
At-Risk
```

Output:

```text
sip_continuity_analysis.csv
```

---

# 🤖 Fund Recommender

A simple risk-based fund recommendation system was developed.

### Input

Risk appetite:

```text
Low
Moderate
High
```

### Output

Top 3 funds ranked by Sharpe Ratio within the matching risk category.

The recommender uses the available:

* Risk grade
* Sharpe Ratio
* Fund information

Script:

```text
scripts/recommender.py
```

Supporting data:

```text
fund_recommender_data.csv
```

---

# 📐 Sector Concentration — HHI

Portfolio concentration was analyzed using the **Herfindahl-Hirschman Index (HHI)**.

The basic calculation is:

```text
HHI = Σ(weightᵢ²)
```

A higher HHI indicates greater concentration.

Output:

```text
sector_hhi_analysis.csv
```

This analysis helps evaluate concentration risk across equity funds.

---

# 📊 Power BI Dashboard

An interactive **4-page Power BI dashboard** was developed.

## Page 1 — Industry Overview

Includes:

* Total AUM
* SIP inflows
* Folios
* Number of schemes
* Industry AUM trend
* AUM by AMC
* Industry-level KPIs

---

## Page 2 — Fund Performance

Includes:

* Average CAGR
* Average Sharpe Ratio
* Average Fund Score
* Return vs Risk scatter plot
* Fund Scorecard
* Fund ranking
* Fund vs benchmark performance
* Fund House slicer
* Category slicer
* Plan slicer
* Scheme slicer

### NAV Drill-through

A dedicated **NAV Detail** page was created.

Users can right-click a fund from the Fund Performance table and drill through to its historical NAV details.

---

## Page 3 — Investor Analytics

Includes:

* Transaction amount by state
* SIP / Lumpsum / Redemption distribution
* Average SIP amount by age group
* Monthly transaction volume

Slicers:

* State
* Age Group
* City Tier

---

## Page 4 — SIP & Market Trends

Includes:

* SIP inflow trend
* NIFTY 50 benchmark trend
* Category inflow analysis
* Category inflow heatmap
* FY25 net inflow by category

The available fund master data currently contains two broad categories, so the dashboard reports the actual available categories rather than artificially creating a Top 5 result.

---

# 🎨 Dashboard Features

The Power BI dashboard includes:

* Interactive slicers
* Drill-through navigation
* KPI cards
* Bar charts
* Line charts
* Donut charts
* Scatter plots
* Matrix heatmap
* Conditional formatting
* Benchmark comparison
* Fund ranking
* Consistent dashboard formatting
* Bluestock branding

---

# 🧪 Quality Assurance

Multiple QA checks were performed throughout the project.

### Fund Scorecard QA

Validated:

* Scorecard shape
* Required columns
* Duplicate AMFI codes
* Missing values
* Fund ranking

### Advanced Analytics QA

Validated:

* VaR/CVaR report
* 40 fund records
* Rolling Sharpe chart
* Investor cohort analysis
* SIP continuity analysis
* Fund recommender dataset
* Sector HHI analysis

### Dashboard QA

Validated:

* Data connections
* Visuals
* Slicers
* Drill-through
* Page formatting
* Dashboard navigation
* Final exports

---

# 💡 Key Business Insights

The project is designed to answer practical investment and business questions such as:

1. Which mutual funds provide the strongest risk-adjusted returns?
2. Which funds have the highest historical downside risk?
3. Which funds show the strongest Alpha relative to their benchmark?
4. Which funds have lower expenses and better overall scores?
5. Which investor cohorts contribute the highest investment amounts?
6. How consistent are investors with their SIP contributions?
7. Which investors may be at risk of discontinuing SIP investments?
8. Which risk categories contain the strongest funds by Sharpe Ratio?
9. Which funds have higher concentration risk?
10. How does SIP inflow movement compare with broader market performance?

---

# 🛠️ Tech Stack

### Programming

* Python
* SQL

### Python Libraries

* Pandas
* NumPy
* Matplotlib
* Plotly
* Requests
* SciPy
* SQLAlchemy

### Data Analysis

* Exploratory Data Analysis
* Financial analytics
* Statistical analysis
* Risk analytics
* Time-series analysis

### Business Intelligence

* Microsoft Power BI
* Tableau

### Database

* MySQL
* SQLite

### Development

* Jupyter Notebook
* VS Code
* Git / GitHub

---

# 📦 Major Deliverables

## Analytics

```text
fund_scorecard.csv
benchmark_summary.csv
tracking_error_comparison.csv
rolling_30d_tracking_difference.csv
normalized_benchmark_performance.csv
```

## Advanced Analytics

```text
var_cvar_report.csv
investor_cohort_analysis.csv
sip_continuity_analysis.csv
fund_recommender_data.csv
sector_hhi_analysis.csv
rolling_sharpe_chart.png
```

## Power BI

```text
bluestock_mf_dashboard.pbix
Dashboard.pdf
Page1_Industry_Overview.png
Page2_Fund_Performance.png
Page3_Investor_Analytics.png
Page4_SIP_Market_Trends.png
```

---

# 🚀 How to Run the Project

## 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd mutual-fund-analysis
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Run the analysis notebooks

Open Jupyter Notebook or VS Code and run the notebooks inside:

```text
notebooks/
```

Recommended workflow:

```text
Data Ingestion
      ↓
Data Cleaning
      ↓
EDA
      ↓
Performance Analytics
      ↓
Benchmark Analysis
      ↓
Fund Scorecard
      ↓
Advanced Analytics
      ↓
Power BI Dashboard
      ↓
Final QA
```

## 4. Run the recommender

From the project root:

```bash
python scripts/recommender.py
```

---

# 📚 Main Notebooks

### Advanced Analytics

```text
notebooks/Advanced_Analytics.ipynb
```

Contains:

* VaR
* CVaR
* Rolling Sharpe
* Investor cohorts
* SIP continuity
* HHI analysis
* Advanced insights

### Performance Analytics

```text
notebooks/Performance_Analytics.ipynb
```

Contains:

* CAGR
* Sharpe
* Sortino
* Alpha
* Beta
* Maximum Drawdown
* Tracking Error

### EDA

```text
notebooks/EDA_Analysis.ipynb
```

Contains:

* NAV analysis
* AUM analysis
* SIP analysis
* Fund-level exploration

### Final QA

```text
notebooks/final_project_qa.ipynb
```

Contains project-level validation checks.

---

# 📈 Project Workflow

```text
                    RAW DATA
                       │
                       ▼
                DATA INGESTION
                       │
                       ▼
                 DATA CLEANING
                       │
                       ▼
                     EDA
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     Performance   Benchmark    Investor
      Analytics     Analysis    Analytics
          │            │            │
          └────────────┼────────────┘
                       ▼
                 FUND SCORECARD
                       │
                       ▼
              ADVANCED ANALYTICS
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
     VaR/CVaR     SIP Continuity    Recommender
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                 POWER BI
                  DASHBOARD
                       │
                       ▼
                 FINAL QA
                       │
                       ▼
              REPORTS & INSIGHTS
```

---

# 🎓 Skills Demonstrated

This project demonstrates practical experience in:

* Data cleaning
* Data preprocessing
* Exploratory Data Analysis
* Financial data analysis
* Risk analysis
* Time-series analysis
* Statistical analysis
* SQL
* Python
* Pandas
* NumPy
* Data visualization
* Power BI
* Tableau
* Dashboard development
* KPI development
* Benchmark analysis
* Investor analytics
* Business intelligence
* Data quality assurance
* Financial decision-support analytics

---

# 👨‍💻 Author

**Rakshit Vegad**

B.E. Information Technology
Shantilal Shah Engineering College

### Areas of Interest

* Data Analytics
* Business Intelligence
* Financial Analytics
* Machine Learning
* Python
* SQL
* Power BI
* Tableau

---

# ⭐ Project Summary

The **Mutual Fund Analytics & Investment Scorecard** project demonstrates an end-to-end data analytics workflow starting from raw financial and investor datasets and progressing through data cleaning, exploratory analysis, performance and risk measurement, benchmark comparison, advanced investor analytics, fund recommendation, and interactive Power BI dashboard development.

The final platform provides a data-driven view of mutual fund performance, investment risk, investor behavior, SIP continuity, benchmark alignment, and overall fund quality.

---
