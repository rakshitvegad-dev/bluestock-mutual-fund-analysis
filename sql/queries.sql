--Query 1 :- Top 5 Funds by AUM--
SELECT scheme_name, aum_crore
FROM scheme_performance
ORDER BY aum_crore DESC
LIMIT 5;


--Query 2 :- Average NAV Per Month
SELECT strftime('%Y-%m', date) AS Month,
AVG(nav) AS Average_NAV
FROM nav_history
GROUP BY Month
ORDER BY Month;


--Query 3 :- SIP Transactions by Year
SELECT strftime('%Y', transaction_date) AS Year,
COUNT(*) AS SIP_Transactions
FROM investor_transactions
WHERE transaction_type='SIP'
GROUP BY Year
ORDER BY Year;


--Query 4 :- Transactions by State
SELECT 
state,
COUNT(*) AS Total_Transactions
FROM investor_transactions
GROUP BY state
ORDER BY Total_Transactions DESC;


--Query 5 :- Funds with Expense Ratio Less Than 1%
SELECT
scheme_name,
expense_ratio_pct
FROM scheme_performance
WHERE expense_ratio_pct < 1;


--Query 6 :- Average 3-Year Return by Category
SELECT
category,
AVG(return_3yr_pct) AS Avg_Return
FROM scheme_performance
GROUP BY category;


--Query 7 :- Top 5 Highest Rated Funds
SELECT
scheme_name,
morningstar_rating
FROM scheme_performance
ORDER BY morningstar_rating DESC
LIMIT 5;


--Query 8 :- Fund Count by Risk Grade
SELECT
risk_grade,
COUNT(*) AS Total_Funds
FROM scheme_performance
GROUP BY risk_grade;


--Query 9 :- Average Transaction Amount by Payment Mode
SELECT
payment_mode,
AVG(amount_inr) AS Average_Amount
FROM investor_transactions
GROUP BY payment_mode;


--Query 10 :- Top 10 Fund Houses by Number of Schemes
SELECT
fund_house,
COUNT(*) AS Total_Schemes
FROM fund_master
GROUP BY fund_house
ORDER BY Total_Schemes DESC
LIMIT 10;