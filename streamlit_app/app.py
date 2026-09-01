"""
Bluestock Mutual Fund Analytics
Streamlit Dashboard

Pages
------
1. Industry Overview
2. Fund Performance
3. Investor Analytics
4. SIP & Market Trends

Additional
----------
- Fund recommender
- Monte Carlo NAV projection
- Markowitz efficient frontier
- SQLite database support
- CSV fallback
- Robust date-column normalization
"""

from pathlib import Path
import sqlite3
import warnings

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

warnings.filterwarnings("ignore")


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Bluestock Mutual Fund Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"

DB_PATH = BASE_DIR / "bluestock_mf.db"


# ============================================================
# GLOBAL STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        color: #666;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        padding: 12px;
        border-radius: 10px;
    }

    div[data-testid="stMetric"] {
        border-radius: 10px;
        padding: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_read_csv(path: Path) -> pd.DataFrame:
    """Read CSV safely."""

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.warning(f"Could not read {path.name}: {exc}")
        return pd.DataFrame()


def normalize_date_column(
    df: pd.DataFrame,
    preferred_columns=None
) -> pd.DataFrame:
    """
    Normalize different possible date column names to 'date'.

    Handles:
        date
        Date
        DATE
        full_date
        nav_date
        transaction_date
        month
    """

    if df.empty:
        return df

    df = df.copy()

    preferred_columns = preferred_columns or [
        "date",
        "Date",
        "DATE",
        "full_date",
        "nav_date",
        "transaction_date",
        "month",
    ]

    found = None

    for column in preferred_columns:
        if column in df.columns:
            found = column
            break

    if found is None:
        # Case-insensitive fallback
        lower_map = {
            str(col).strip().lower(): col
            for col in df.columns
        }

        for candidate in [
            "date",
            "full_date",
            "nav_date",
            "transaction_date",
            "month",
        ]:
            if candidate in lower_map:
                found = lower_map[candidate]
                break

    if found is not None and found != "date":
        df = df.rename(columns={found: "date"})

    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

    return df


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names."""

    if df.empty:
        return df

    df = df.copy()

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    return df


def format_inr(value) -> str:
    """Format Indian currency."""

    if pd.isna(value):
        return "₹0"

    value = float(value)

    if abs(value) >= 1e7:
        return f"₹{value / 1e7:.2f} Cr"

    if abs(value) >= 1e5:
        return f"₹{value / 1e5:.2f} L"

    return f"₹{value:,.0f}"


def first_existing_column(df, candidates):
    """Return first existing column."""

    for column in candidates:
        if column in df.columns:
            return column

    return None


# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data
def load_fund_master():

    paths = [
        RAW_DIR / "fund_master.csv",
        RAW_DIR / "01_fund_master.csv",
        PROCESSED_DIR / "fund_master.csv",
    ]

    for path in paths:

        df = safe_read_csv(path)

        if not df.empty:

            df = clean_columns(df)

            if "amfi_code" in df.columns:
                df["amfi_code"] = pd.to_numeric(
                    df["amfi_code"],
                    errors="coerce"
                )

            return df

    return pd.DataFrame()


@st.cache_data
def load_nav():

    paths = [
        PROCESSED_DIR / "nav_history_cleaned.csv",
        RAW_DIR / "nav_history.csv",
    ]

    for path in paths:

        df = safe_read_csv(path)

        if not df.empty:

            df = clean_columns(df)

            df = normalize_date_column(df)

            if "amfi_code" in df.columns:
                df["amfi_code"] = pd.to_numeric(
                    df["amfi_code"],
                    errors="coerce"
                )

            if "nav" in df.columns:
                df["nav"] = pd.to_numeric(
                    df["nav"],
                    errors="coerce"
                )

            df = df.dropna(
                subset=["date", "amfi_code", "nav"]
            )

            return df

    return pd.DataFrame()


@st.cache_data
def load_performance():

    path = PROCESSED_DIR / "cleaned_scheme_performance.csv"

    df = safe_read_csv(path)

    if df.empty:
        return df

    df = clean_columns(df)

    if "amfi_code" in df.columns:
        df["amfi_code"] = pd.to_numeric(
            df["amfi_code"],
            errors="coerce"
        )

    numeric_columns = [
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "expense_ratio_pct",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


@st.cache_data
def load_transactions():

    path = PROCESSED_DIR / "investor_transactions_cleaned.csv"

    df = safe_read_csv(path)

    if df.empty:
        path = RAW_DIR / "investor_transactions.csv"
        df = safe_read_csv(path)

    if df.empty:
        return df

    df = clean_columns(df)

    df = normalize_date_column(
        df,
        [
            "transaction_date",
            "date",
            "Date",
        ],
    )

    if "amount_inr" in df.columns:
        df["amount_inr"] = pd.to_numeric(
            df["amount_inr"],
            errors="coerce"
        )

    return df


@st.cache_data
def load_aum():

    paths = [
        RAW_DIR / "aum.csv",
        RAW_DIR / "AUM.csv",
        PROCESSED_DIR / "aum.csv",
    ]

    for path in paths:

        df = safe_read_csv(path)

        if not df.empty:

            df = clean_columns(df)

            df = normalize_date_column(df)

            return df

    return pd.DataFrame()


@st.cache_data
def load_sip():

    paths = [
        RAW_DIR / "monthly_sip_inflows.csv",
        RAW_DIR / "04_monthly_sip_inflows.csv",
        RAW_DIR / "sip.csv",
        PROCESSED_DIR / "monthly_sip_inflows.csv",
    ]

    for path in paths:

        df = safe_read_csv(path)

        if not df.empty:

            df = clean_columns(df)

            df = normalize_date_column(
                df,
                ["month", "date", "Date"]
            )

            return df

    return pd.DataFrame()


# ============================================================
# SQLITE LOADER
# ============================================================

@st.cache_data
def load_sqlite_table(table_name):

    if not DB_PATH.exists():
        return pd.DataFrame()

    try:

        connection = sqlite3.connect(DB_PATH)

        df = pd.read_sql_query(
            f"SELECT * FROM {table_name}",
            connection
        )

        connection.close()

        return df

    except Exception:
        return pd.DataFrame()


# ============================================================
# LOAD DATA
# ============================================================

fund_master = load_fund_master()
nav = load_nav()
performance = load_performance()
transactions = load_transactions()
aum = load_aum()
sip = load_sip()


# ============================================================
# DATABASE FALLBACK
# ============================================================

if fund_master.empty:
    fund_master = load_sqlite_table("dim_fund")

if nav.empty:

    nav = load_sqlite_table("fact_nav")

    if not nav.empty:

        nav = normalize_date_column(nav)

        if "date_key" in nav.columns and "date" not in nav.columns:

            dates = load_sqlite_table("dim_date")

            if not dates.empty:

                dates = normalize_date_column(
                    dates,
                    ["full_date", "date"]
                )

                if "date_key" in dates.columns:

                    nav = nav.merge(
                        dates[
                            ["date_key", "date"]
                        ],
                        on="date_key",
                        how="left"
                    )


if performance.empty:
    performance = load_sqlite_table(
        "fact_performance"
    )

if transactions.empty:
    transactions = load_sqlite_table(
        "fact_transactions"
    )

if aum.empty:
    aum = load_sqlite_table("fact_aum")


# ============================================================
# MERGE FUND INFORMATION
# ============================================================

def merge_fund_information(df):

    if df.empty or fund_master.empty:
        return df

    if "amfi_code" not in df.columns:
        return df

    if "amfi_code" not in fund_master.columns:
        return df

    master_columns = [
        "amfi_code",
        "scheme_name",
        "fund_house",
        "category",
        "sub_category",
        "plan",
        "risk_category",
    ]

    master_columns = [
        col
        for col in master_columns
        if col in fund_master.columns
    ]

    master = fund_master[
        master_columns
    ].drop_duplicates(
        subset=["amfi_code"]
    )

    return df.merge(
        master,
        on="amfi_code",
        how="left",
        suffixes=("", "_master")
    )


nav = merge_fund_information(nav)
performance = merge_fund_information(performance)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">📊 Bluestock Mutual Fund Analytics</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">End-to-end mutual fund analytics, performance, risk and investor insights</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Industry Overview",
        "Fund Performance",
        "Investor Analytics",
        "SIP & Market Trends",
        "Advanced Analytics",
    ]
)


# ============================================================
# INDUSTRY OVERVIEW
# ============================================================

if page == "Industry Overview":

    st.header("🏦 Industry Overview")

    col1, col2, col3, col4 = st.columns(4)

    total_schemes = (
        fund_master["amfi_code"].nunique()
        if "amfi_code" in fund_master.columns
        else 0
    )

    total_funds = total_schemes

    total_investors = (
        transactions["investor_id"].nunique()
        if "investor_id" in transactions.columns
        else 0
    )

    total_aum = None

    if not aum.empty:

        if "aum_crore" in aum.columns:

            total_aum = aum[
                "aum_crore"
            ].sum()

        elif "aum_lakh_crore" in aum.columns:

            total_aum = (
                aum["aum_lakh_crore"].sum()
                * 100000
            )

    with col1:
        st.metric(
            "Total Schemes",
            f"{total_schemes:,}"
        )

    with col2:
        st.metric(
            "Total Investors",
            f"{total_investors:,}"
        )

    with col3:
        st.metric(
            "Fund Houses",
            (
                fund_master["fund_house"].nunique()
                if "fund_house" in fund_master.columns
                else 0
            )
        )

    with col4:

        if total_aum is not None:

            st.metric(
                "AUM",
                f"₹{total_aum:,.0f} Cr"
            )

        else:

            st.metric(
                "AUM",
                "N/A"
            )


    st.divider()


    # -----------------------------
    # AUM BY FUND HOUSE
    # -----------------------------

    if not aum.empty:

        st.subheader(
            "AUM by Asset Management Company"
        )

        if "fund_house" in aum.columns:

            aum_column = first_existing_column(
                aum,
                [
                    "aum_crore",
                    "aum_lakh_crore",
                ]
            )

            if aum_column:

                temp = (
                    aum
                    .groupby("fund_house")[
                        aum_column
                    ]
                    .sum()
                    .reset_index()
                )

                if aum_column == "aum_lakh_crore":
                    temp["AUM"] = (
                        temp[aum_column] * 100000
                    )
                else:
                    temp["AUM"] = temp[aum_column]

                temp = temp.sort_values(
                    "AUM",
                    ascending=False
                )

                fig = px.bar(
                    temp,
                    x="fund_house",
                    y="AUM",
                    title="AUM by Fund House",
                    labels={
                        "fund_house": "Fund House",
                        "AUM": "AUM (₹ Cr)",
                    },
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


    # -----------------------------
    # RISK DISTRIBUTION
    # -----------------------------

    if "risk_category" in fund_master.columns:

        st.subheader(
            "Risk Grade Distribution"
        )

        risk = (
            fund_master["risk_category"]
            .value_counts()
            .reset_index()
        )

        risk.columns = [
            "risk_category",
            "count"
        ]

        fig = px.pie(
            risk,
            names="risk_category",
            values="count",
            hole=0.45,
            title="Fund Risk Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# FUND PERFORMANCE
# ============================================================

elif page == "Fund Performance":

    st.header("📈 Fund Performance")

    if performance.empty:

        st.error(
            "Performance dataset could not be loaded."
        )
        st.stop()


    # -----------------------------
    # FILTERS
    # -----------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        fund_houses = ["All"]

        if "fund_house" in performance.columns:

            fund_houses += sorted(
                performance[
                    "fund_house"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_house = st.selectbox(
            "Fund House",
            fund_houses
        )


    with col2:

        categories = ["All"]

        if "category" in performance.columns:

            categories += sorted(
                performance[
                    "category"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_category = st.selectbox(
            "Category",
            categories
        )


    with col3:

        plans = ["All"]

        if "plan" in performance.columns:

            plans += sorted(
                performance[
                    "plan"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_plan = st.selectbox(
            "Plan",
            plans
        )


    with col4:

        schemes = ["All"]

        if "scheme_name" in performance.columns:

            schemes += sorted(
                performance[
                    "scheme_name"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_scheme = st.selectbox(
            "Scheme",
            schemes
        )


    filtered = performance.copy()


    if selected_house != "All":
        filtered = filtered[
            filtered["fund_house"]
            == selected_house
        ]


    if selected_category != "All":
        filtered = filtered[
            filtered["category"]
            == selected_category
        ]


    if selected_plan != "All":
        filtered = filtered[
            filtered["plan"]
            == selected_plan
        ]


    if selected_scheme != "All":
        filtered = filtered[
            filtered["scheme_name"]
            == selected_scheme
        ]


    # -----------------------------
    # KPIs
    # -----------------------------

    c1, c2, c3 = st.columns(3)

    with c1:

        value = (
            filtered["return_3yr_pct"].mean()
            if "return_3yr_pct" in filtered.columns
            else 0
        )

        st.metric(
            "Average 3Y Return",
            f"{value:.2f}%"
        )


    with c2:

        value = (
            filtered["sharpe_ratio"].mean()
            if "sharpe_ratio" in filtered.columns
            else 0
        )

        st.metric(
            "Average Sharpe",
            f"{value:.2f}"
        )


    with c3:

        value = (
            filtered["max_drawdown_pct"].mean()
            if "max_drawdown_pct"
            in filtered.columns
            else 0
        )

        st.metric(
            "Average Max Drawdown",
            f"{value:.2f}%"
        )


    st.divider()


    # -----------------------------
    # TOP FUNDS
    # -----------------------------

    if "sharpe_ratio" in filtered.columns:

        st.subheader(
            "Top Funds by Sharpe Ratio"
        )

        top = (
            filtered
            .sort_values(
                "sharpe_ratio",
                ascending=False
            )
            .head(10)
        )

        if not top.empty:

            fig = px.bar(
                top,
                x="sharpe_ratio",
                y="scheme_name",
                orientation="h",
                title="Top 10 Funds by Sharpe Ratio",
                labels={
                    "sharpe_ratio": "Sharpe Ratio",
                    "scheme_name": "Fund",
                },
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # -----------------------------
    # RETURN VS RISK
    # -----------------------------

    if {
        "return_3yr_pct",
        "std_dev_ann_pct",
    }.issubset(filtered.columns):

        st.subheader(
            "Return vs Risk"
        )

        plot_data = filtered.copy()

        fig = px.scatter(
            plot_data,
            x="std_dev_ann_pct",
            y="return_3yr_pct",
            hover_name=(
                "scheme_name"
                if "scheme_name"
                in plot_data.columns
                else None
            ),
            title="3-Year Return vs Annualised Volatility",
            labels={
                "std_dev_ann_pct":
                    "Annualised Volatility (%)",
                "return_3yr_pct":
                    "3-Year Return (%)",
            },
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # -----------------------------
    # PERFORMANCE TABLE
    # -----------------------------

    st.subheader(
        "Fund Performance Scorecard"
    )

    display_columns = [
        "scheme_name",
        "fund_house",
        "category",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "max_drawdown_pct",
    ]

    display_columns = [
        col
        for col in display_columns
        if col in filtered.columns
    ]

    st.dataframe(
        filtered[display_columns],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# INVESTOR ANALYTICS
# ============================================================

elif page == "Investor Analytics":

    st.header("👥 Investor Analytics")

    if transactions.empty:

        st.error(
            "Investor transaction dataset could not be loaded."
        )
        st.stop()


    # -----------------------------
    # FILTERS
    # -----------------------------

    col1, col2, col3 = st.columns(3)


    with col1:

        states = ["All"]

        if "state" in transactions.columns:

            states += sorted(
                transactions[
                    "state"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_state = st.selectbox(
            "State",
            states
        )


    with col2:

        ages = ["All"]

        if "age_group" in transactions.columns:

            ages += sorted(
                transactions[
                    "age_group"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_age = st.selectbox(
            "Age Group",
            ages
        )


    with col3:

        tiers = ["All"]

        if "city_tier" in transactions.columns:

            tiers += sorted(
                transactions[
                    "city_tier"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_tier = st.selectbox(
            "City Tier",
            tiers
        )


    filtered = transactions.copy()


    if selected_state != "All":
        filtered = filtered[
            filtered["state"]
            == selected_state
        ]


    if selected_age != "All":
        filtered = filtered[
            filtered["age_group"]
            == selected_age
        ]


    if selected_tier != "All":
        filtered = filtered[
            filtered["city_tier"]
            == selected_tier
        ]


    # -----------------------------
    # KPIs
    # -----------------------------

    c1, c2, c3 = st.columns(3)


    with c1:

        investors = (
            filtered["investor_id"].nunique()
            if "investor_id"
            in filtered.columns
            else 0
        )

        st.metric(
            "Investors",
            f"{investors:,}"
        )


    with c2:

        total = (
            filtered["amount_inr"].sum()
            if "amount_inr"
            in filtered.columns
            else 0
        )

        st.metric(
            "Transaction Value",
            format_inr(total)
        )


    with c3:

        avg = (
            filtered["amount_inr"].mean()
            if "amount_inr"
            in filtered.columns
            else 0
        )

        st.metric(
            "Average Transaction",
            format_inr(avg)
        )


    st.divider()


    # -----------------------------
    # TRANSACTION TYPES
    # -----------------------------

    if "transaction_type" in filtered.columns:

        type_data = (
            filtered[
                "transaction_type"
            ]
            .value_counts()
            .reset_index()
        )

        type_data.columns = [
            "transaction_type",
            "count"
        ]

        fig = px.pie(
            type_data,
            names="transaction_type",
            values="count",
            hole=0.45,
            title="Transaction Type Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # -----------------------------
    # STATE TRANSACTIONS
    # -----------------------------

    if {
        "state",
        "amount_inr"
    }.issubset(filtered.columns):

        state_data = (
            filtered
            .groupby("state")[
                "amount_inr"
            ]
            .sum()
            .reset_index()
            .sort_values(
                "amount_inr",
                ascending=False
            )
            .head(15)
        )

        fig = px.bar(
            state_data,
            x="amount_inr",
            y="state",
            orientation="h",
            title="Transaction Value by State",
            labels={
                "amount_inr":
                    "Transaction Value (₹)",
                "state": "State",
            },
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # -----------------------------
    # AGE GROUP
    # -----------------------------

    if {
        "age_group",
        "amount_inr"
    }.issubset(filtered.columns):

        age_data = (
            filtered
            .groupby("age_group")[
                "amount_inr"
            ]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            age_data,
            x="age_group",
            y="amount_inr",
            title="Average Transaction by Age Group",
            labels={
                "age_group": "Age Group",
                "amount_inr":
                    "Average Transaction (₹)",
            },
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# SIP & MARKET TRENDS
# ============================================================

elif page == "SIP & Market Trends":

    st.header("💰 SIP & Market Trends")


    # -----------------------------
    # SIP INFLOWS
    # -----------------------------

    if not sip.empty:

        st.subheader(
            "Monthly SIP Inflow"
        )

        if "date" in sip.columns:

            sip_plot = sip.copy()

            sip_plot = sip_plot.dropna(
                subset=["date"]
            )

            sip_plot = sip_plot.sort_values(
                "date"
            )

            if "sip_inflow_crore" in sip_plot.columns:

                fig = px.line(
                    sip_plot,
                    x="date",
                    y="sip_inflow_crore",
                    title="Monthly SIP Inflow",
                    labels={
                        "date": "Month",
                        "sip_inflow_crore":
                            "SIP Inflow (₹ Cr)",
                    },
                )

                fig.update_traces(
                    mode="lines+markers"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


        # SIP KPI

        if "sip_inflow_crore" in sip.columns:

            latest = (
                sip.sort_values("date")
                .iloc[-1]
            )

            st.metric(
                "Latest SIP Inflow",
                f"₹{latest['sip_inflow_crore']:,.0f} Cr"
            )


    else:

        st.info(
            "SIP dataset not available."
        )


    # ========================================================
    # NAV ANALYSIS
    # ========================================================

    st.divider()

    st.subheader(
        "NAV Trend Analysis"
    )


    if nav.empty:

        st.warning(
            "NAV dataset not available."
        )

    else:

        # -----------------------------
        # NAV FILTER
        # -----------------------------

        available_schemes = ["All"]

        if "scheme_name" in nav.columns:

            available_schemes += sorted(
                nav[
                    "scheme_name"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_nav_scheme = st.selectbox(
            "Select Scheme",
            available_schemes
        )


        nav_filtered = nav.copy()


        if selected_nav_scheme != "All":

            nav_filtered = nav_filtered[
                nav_filtered[
                    "scheme_name"
                ]
                == selected_nav_scheme
            ]


        # IMPORTANT:
        # Always normalize date before sorting.

        nav_filtered = normalize_date_column(
            nav_filtered
        )


        if "date" not in nav_filtered.columns:

            st.error(
                "NAV data does not contain a usable date column."
            )

        else:

            nav_filtered = nav_filtered.dropna(
                subset=["date"]
            )

            nav_filtered = nav_filtered.sort_values(
                "date"
            )


            if {
                "date",
                "nav"
            }.issubset(nav_filtered.columns):

                fig = px.line(
                    nav_filtered,
                    x="date",
                    y="nav",
                    color=(
                        "scheme_name"
                        if (
                            selected_nav_scheme
                            == "All"
                            and
                            "scheme_name"
                            in nav_filtered.columns
                        )
                        else None
                    ),
                    title="NAV Trend",
                    labels={
                        "date": "Date",
                        "nav": "NAV (₹)",
                    },
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


# ============================================================
# ADVANCED ANALYTICS
# ============================================================

else:

    st.header("🚀 Advanced Analytics")


    tabs = st.tabs(
        [
            "Fund Recommender",
            "Monte Carlo",
            "Markowitz",
        ]
    )


    # ========================================================
    # RECOMMENDER
    # ========================================================

    with tabs[0]:

        st.subheader(
            "🤖 Mutual Fund Recommender"
        )

        recommender_path = (
            BASE_DIR
            / "fund_recommender_data.csv"
        )

        recommender = safe_read_csv(
            recommender_path
        )

        if recommender.empty:

            st.warning(
                "fund_recommender_data.csv not found."
            )

        else:

            risk_options = [
                "Low",
                "Moderate",
                "High",
            ]

            risk = st.selectbox(
                "Select Risk Appetite",
                risk_options
            )

            if "risk_grade" in recommender.columns:

                result = recommender[
                    recommender[
                        "risk_grade"
                    ]
                    == risk
                ].copy()

                if "Sharpe_Ratio" in result.columns:

                    result["Sharpe_Ratio"] = pd.to_numeric(
                        result["Sharpe_Ratio"],
                        errors="coerce"
                    )

                    result = (
                        result
                        .dropna(
                            subset=[
                                "Sharpe_Ratio"
                            ]
                        )
                        .sort_values(
                            "Sharpe_Ratio",
                            ascending=False
                        )
                        .head(3)
                    )

                st.write(
                    f"### Top 3 Funds — {risk} Risk"
                )

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True
                )


    # ========================================================
    # MONTE CARLO
    # ========================================================

    with tabs[1]:

        st.subheader(
            "🎲 Monte Carlo NAV Projection"
        )

        mc_path = (
            PROCESSED_DIR
            / "monte_carlo_nav_simulation.csv"
        )

        mc = safe_read_csv(
            mc_path
        )

        if mc.empty:

            st.warning(
                "Monte Carlo simulation output not found."
            )

        else:

            st.success(
                "Monte Carlo simulation data loaded."
            )

            st.dataframe(
                mc.head(20),
                use_container_width=True,
                hide_index=True
            )

            # Try to identify percentile columns

            percentile_columns = [
                col
                for col in mc.columns
                if any(
                    key in str(col).lower()
                    for key in [
                        "5%",
                        "50%",
                        "95%",
                        "median",
                        "percentile",
                    ]
                )
            ]

            if percentile_columns:

                st.write(
                    "Simulation percentile outputs:"
                )

                st.write(
                    percentile_columns
                )


            chart_path = (
                REPORTS_DIR
                / "monte_carlo_nav_projection.png"
            )

            if chart_path.exists():

                st.image(
                    str(chart_path),
                    caption="5-Year Monte Carlo NAV Projection"
                )


    # ========================================================
    # MARKOWITZ
    # ========================================================

    with tabs[2]:

        st.subheader(
            "📐 Markowitz Efficient Frontier"
        )

        portfolio_path = (
            PROCESSED_DIR
            / "markowitz_portfolios.csv"
        )

        portfolio = safe_read_csv(
            portfolio_path
        )

        if portfolio.empty:

            st.warning(
                "Markowitz portfolio output not found."
            )

        else:

            st.success(
                "Markowitz portfolio data loaded."
            )

            st.dataframe(
                portfolio.head(20),
                use_container_width=True,
                hide_index=True
            )

            # Detect portfolio columns

            x_col = first_existing_column(
                portfolio,
                [
                    "volatility",
                    "portfolio_volatility",
                    "risk",
                    "std_dev",
                ]
            )

            y_col = first_existing_column(
                portfolio,
                [
                    "return",
                    "portfolio_return",
                    "expected_return",
                ]
            )

            if x_col and y_col:

                portfolio[x_col] = pd.to_numeric(
                    portfolio[x_col],
                    errors="coerce"
                )

                portfolio[y_col] = pd.to_numeric(
                    portfolio[y_col],
                    errors="coerce"
                )

                plot_df = portfolio.dropna(
                    subset=[
                        x_col,
                        y_col
                    ]
                )

                fig = px.scatter(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    title="Markowitz Efficient Frontier",
                    labels={
                        x_col: "Portfolio Risk",
                        y_col: "Portfolio Return",
                    },
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            frontier_path = (
                REPORTS_DIR
                / "markowitz_efficient_frontier.png"
            )

            if frontier_path.exists():

                st.image(
                    str(frontier_path),
                    caption="Markowitz Efficient Frontier"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Bluestock Mutual Fund Analytics | "
    "Historical analytics only — not individualized investment advice."
)