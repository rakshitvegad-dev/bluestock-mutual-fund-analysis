SELECT
    fund_house,
    SUM(aum_crore) AS total_aum_crore
FROM fact_aum
GROUP BY fund_house
ORDER BY total_aum_crore DESC
LIMIT 5;

-- ============================================================
-- QUERY 2: Average NAV per Month
-- ============================================================

SELECT
    d.year,
    d.month,
    d.month_name,
    AVG(n.nav) AS average_nav
FROM fact_nav n
JOIN dim_date d
    ON n.date_key = d.date_key
GROUP BY
    d.year,
    d.month,
    d.month_name
ORDER BY
    d.year,
    d.month;

-- ============================================================
-- QUERY 3: SIP Inflow Year-over-Year Growth
-- ============================================================

WITH yearly_sip AS (
    SELECT
        strftime('%Y', month) AS year,
        SUM(sip_inflow_crore) AS total_sip_inflow_crore
    FROM monthly_sip_inflow
    GROUP BY strftime('%Y', month)
)

SELECT
    year,
    ROUND(total_sip_inflow_crore, 2) AS total_sip_inflow_crore,

    LAG(
        ROUND(total_sip_inflow_crore, 2)
    ) OVER (
        ORDER BY year
    ) AS previous_year_inflow,

    ROUND(
        (
            total_sip_inflow_crore
            - LAG(total_sip_inflow_crore) OVER (ORDER BY year)
        )
        /
        LAG(total_sip_inflow_crore) OVER (ORDER BY year)
        * 100,
        2
    ) AS yoy_growth_pct

FROM yearly_sip
ORDER BY year;

-- ============================================================
-- QUERY 4: Total Transaction Amount by State
-- ============================================================

SELECT
    state,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_transaction_amount
FROM fact_transactions
WHERE state IS NOT NULL
GROUP BY state
ORDER BY total_transaction_amount DESC;

-- ============================================================
-- QUERY 5: Funds with Expense Ratio Below 1%
-- ============================================================

SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    sub_category,
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- ============================================================
-- QUERY 6: Top 5 Funds by 3-Year Return
-- ============================================================

SELECT
    amfi_code,
    scheme_name,
    fund_house,
    return_3yr_pct
FROM fact_performance
ORDER BY return_3yr_pct DESC
LIMIT 5;


-- ============================================================
-- QUERY 7: Top 5 Funds by Sharpe Ratio
-- ============================================================

SELECT
    amfi_code,
    scheme_name,
    fund_house,
    sharpe_ratio,
    risk_grade
FROM fact_performance
ORDER BY sharpe_ratio DESC
LIMIT 5;


-- ============================================================
-- QUERY 8: Funds with Lowest Maximum Drawdown
-- ============================================================

SELECT
    amfi_code,
    scheme_name,
    fund_house,
    max_drawdown_pct
FROM fact_performance
ORDER BY max_drawdown_pct DESC
LIMIT 5;


-- ============================================================
-- QUERY 9: Average Transaction Amount by Transaction Type
-- ============================================================

SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    ROUND(AVG(amount_inr), 2) AS average_transaction_amount,
    ROUND(SUM(amount_inr), 2) AS total_transaction_amount
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_transaction_amount DESC;


-- ============================================================
-- QUERY 10: Fund House Performance Summary
-- ============================================================

SELECT
    d.fund_house,
    COUNT(*) AS number_of_funds,
    ROUND(AVG(p.return_3yr_pct), 2) AS avg_3yr_return,
    ROUND(AVG(p.sharpe_ratio), 2) AS avg_sharpe_ratio,
    ROUND(AVG(p.expense_ratio_pct), 2) AS avg_expense_ratio
FROM fact_performance p
JOIN dim_fund d
    ON p.amfi_code = d.amfi_code
GROUP BY d.fund_house
ORDER BY avg_3yr_return DESC;