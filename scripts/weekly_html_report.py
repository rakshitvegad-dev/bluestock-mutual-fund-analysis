"""
Bluestock Mutual Fund Analytics
Bonus B5 - Automated Weekly HTML Performance Report

Generates an email-ready HTML report from the project's
existing analytics CSV outputs.

No credentials or email passwords are stored in this script.
"""

from pathlib import Path
from datetime import datetime

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"

OUTPUT_HTML = REPORTS_DIR / "weekly_performance_report.html"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_csv(filename: str) -> pd.DataFrame | None:
    """Load a CSV if it exists."""

    path = PROCESSED_DIR / filename

    if not path.exists():
        print(f"WARNING: {filename} not found.")
        return None

    try:
        return pd.read_csv(path)
    except Exception as exc:
        print(f"WARNING: Could not read {filename}: {exc}")
        return None


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find the first matching column from a list of candidates."""

    normalized = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]

    return None


def format_percent(value) -> str:
    """Format a numeric value as a percentage."""

    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "N/A"


def format_number(value) -> str:
    """Format a numeric value."""

    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


# ============================================================
# REPORT SECTIONS
# ============================================================

def performance_section() -> str:
    """Create fund performance section."""

    df = load_csv("cleaned_scheme_performance.csv")

    if df is None or df.empty:
        return "<p>Performance data unavailable.</p>"

    scheme_col = find_column(
        df,
        ["scheme_name"]
    )

    return_col = find_column(
        df,
        ["return_1yr_pct", "return_1yr"]
    )

    sharpe_col = find_column(
        df,
        ["sharpe_ratio", "Sharpe_Ratio"]
    )

    if scheme_col is None:
        return "<p>Scheme name column unavailable.</p>"

    columns = [scheme_col]

    if return_col:
        columns.append(return_col)

    if sharpe_col:
        columns.append(sharpe_col)

    table = df[columns].copy()

    if return_col:
        table = table.sort_values(
            return_col,
            ascending=False
        ).head(10)

    rename_map = {
        scheme_col: "Fund"
    }

    if return_col:
        rename_map[return_col] = "1-Year Return"

    if sharpe_col:
        rename_map[sharpe_col] = "Sharpe Ratio"

    table = table.rename(
        columns=rename_map
    )

    if return_col:
        table["1-Year Return"] = table[
            "1-Year Return"
        ].apply(format_percent)

    if sharpe_col:
        table["Sharpe Ratio"] = table[
            "Sharpe Ratio"
        ].apply(format_number)

    return table.to_html(
        index=False,
        classes="data-table",
        border=0
    )


def sharpe_section() -> str:
    """Create Sharpe ratio section."""

    df = load_csv("sharpe_ratio.csv")

    if df is None or df.empty:
        return "<p>Sharpe ratio data unavailable.</p>"

    scheme_col = find_column(
        df,
        ["scheme_name"]
    )

    sharpe_col = find_column(
        df,
        ["Sharpe_Ratio", "sharpe_ratio"]
    )

    if scheme_col is None or sharpe_col is None:
        return "<p>Required Sharpe columns unavailable.</p>"

    table = (
        df[
            [scheme_col, sharpe_col]
        ]
        .sort_values(
            sharpe_col,
            ascending=False
        )
        .head(10)
        .copy()
    )

    table = table.rename(
        columns={
            scheme_col: "Fund",
            sharpe_col: "Sharpe Ratio"
        }
    )

    table["Sharpe Ratio"] = table[
        "Sharpe Ratio"
    ].apply(format_number)

    return table.to_html(
        index=False,
        classes="data-table",
        border=0
    )


def risk_section() -> str:
    """Create VaR/CVaR risk section."""

    path = REPORTS_DIR / "var_cvar_report.csv"

    if not path.exists():
        return "<p>VaR/CVaR report unavailable.</p>"

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return f"<p>Unable to read VaR/CVaR report: {exc}</p>"

    if df.empty:
        return "<p>VaR/CVaR report is empty.</p>"

    return df.head(10).to_html(
        index=False,
        classes="data-table",
        border=0
    )


def drawdown_section() -> str:
    """Create maximum drawdown section."""

    df = load_csv("maximum_drawdown.csv")

    if df is None or df.empty:
        return "<p>Maximum drawdown data unavailable.</p>"

    return df.head(10).to_html(
        index=False,
        classes="data-table",
        border=0
    )


def monte_carlo_section() -> str:
    """Create Monte Carlo projection section."""

    df = load_csv(
        "monte_carlo_nav_simulation.csv"
    )

    if df is None or df.empty:
        return "<p>Monte Carlo projection unavailable.</p>"

    last = df.iloc[-1]

    p05 = last.get("nav_p05")
    median = last.get("nav_median")
    p95 = last.get("nav_p95")

    return f"""
    <div class="metrics">
        <div class="metric">
            <strong>5th percentile</strong>
            <span>₹{format_number(p05)}</span>
        </div>

        <div class="metric">
            <strong>Median NAV</strong>
            <span>₹{format_number(median)}</span>
        </div>

        <div class="metric">
            <strong>95th percentile</strong>
            <span>₹{format_number(p95)}</span>
        </div>
    </div>
    """


# ============================================================
# BUILD HTML
# ============================================================

def build_report() -> str:
    """Build complete HTML report."""

    generated_at = datetime.now().strftime(
        "%d %B %Y, %I:%M %p"
    )

    return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
Bluestock Mutual Fund Weekly Performance Report
</title>

<style>

body {{
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #222;
    max-width: 1100px;
    margin: 40px auto;
    padding: 0 20px;
}}

h1 {{
    margin-bottom: 5px;
}}

h2 {{
    margin-top: 35px;
    border-bottom: 1px solid #ddd;
    padding-bottom: 8px;
}}

.subtitle {{
    color: #666;
}}

.data-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}}

.data-table th,
.data-table td {{
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}}

.data-table th {{
    font-weight: bold;
}}

.metrics {{
    display: flex;
    gap: 20px;
    margin: 20px 0;
}}

.metric {{
    border: 1px solid #ddd;
    padding: 18px;
    flex: 1;
}}

.metric strong {{
    display: block;
}}

.metric span {{
    display: block;
    font-size: 22px;
    margin-top: 5px;
}}

.footer {{
    margin-top: 40px;
    padding-top: 15px;
    border-top: 1px solid #ddd;
    color: #666;
    font-size: 13px;
}}

</style>

</head>

<body>

<h1>
Bluestock Mutual Fund Weekly Performance Report
</h1>

<p class="subtitle">
Generated automatically on {generated_at}
</p>


<h2>
Top Fund Performance
</h2>

{performance_section()}


<h2>
Top Sharpe Ratios
</h2>

{sharpe_section()}


<h2>
Risk Analysis — VaR / CVaR
</h2>

{risk_section()}


<h2>
Maximum Drawdown
</h2>

{drawdown_section()}


<h2>
5-Year Monte Carlo Projection
</h2>

{monte_carlo_section()}


<div class="footer">

<p>
This report is generated automatically from the
Bluestock Mutual Fund Analytics project.
</p>

<p>
For analytical purposes only. Not investment advice.
</p>

</div>

</body>

</html>
"""


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 70)
    print("BLUESTOCK WEEKLY HTML PERFORMANCE REPORT")
    print("=" * 70)

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    html = build_report()

    OUTPUT_HTML.write_text(
        html,
        encoding="utf-8"
    )

    print(
        f"\nReport generated successfully:"
    )

    print(
        OUTPUT_HTML
    )

    print(
        f"Report size: {OUTPUT_HTML.stat().st_size:,} bytes"
    )


if __name__ == "__main__":
    main()