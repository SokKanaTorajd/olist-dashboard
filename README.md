# Olist E-Commerce Analytics Dashboard

A modular business intelligence dashboard built with **Streamlit**, **DuckDB**, **Pandas**, and **Plotly** using the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The dashboard examines historical product sales, payments, delivery performance, customer reviews, seller performance, and time-based trends. Figures describe marketplace transactions, **not Olist's recognized platform revenue**.

## Dashboard

| Tab | What it shows |
| --- | --- |
| Executive Overview | Product GMV, orders, AOV, unique buyers, item volume, basket size, monthly sales, and leading product categories. |
| Revenue & Payments | Product sales, freight billed, illustrative sales less freight, payment methods, installments, and sales by buyer state. |
| Operations & Logistics | Delivery duration, delivered-order SLA, fulfilled-item proxy, freight per item, and regional freight versus product price. |
| Customer Experience | Review volume, average score, positive review share, score distribution, and delivery timeliness versus ratings. |
| Marketplace & Sellers | Active sellers, seller GMV, seller concentration, dynamic seller quartiles, leading sellers, and seller-state performance. |
| Time Intelligence | Historical MTD/YTD sales, comparable prior-year periods, YoY growth, and monthly GMV comparison. |
| Data Explorer | Independent CSV/DuckDB exploration, filtering, data quality checks, and data previews. |

Global business-tab filters cover **order status** (default: delivered) and **buyer state** (default: all states). Clearing either selection means all available values. The Data Explorer has separate filters. Seller geography uses seller location; the global state filter always refers to buyer location.

## Data source and setup

**Source:** [Brazilian E-Commerce Public Dataset by Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Download and extract the original CSV files locally; raw data and `olist.duckdb` are not required in the Git repository.

**Requirements:** Python, the packages in `requirements.txt`, and the downloaded dataset.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Edit `DATA_DIR` in `ingest.py` to point to the folder containing the Kaggle CSV files. The current script uses a machine-specific Windows path; it is **not portable without updating that setting**. From the project root, run:

```bash
python ingest.py
python build_facts.py
streamlit run app.py
```

Stop Streamlit before rebuilding the DuckDB database so its read-only connection does not interfere with writes. If the raw CSVs have already been ingested and only the fact-table SQL changes, rerun `build_facts.py` without rerunning ingestion.

### Data pipeline

1. **`ingest.py` — raw ingestion.** Loads the Olist CSV files into `olist.duckdb` as `orders`, `order_items`, `order_payments`, `reviews`, `products`, `product_category_translation`, `customers`, `sellers`, and `geolocation`. Existing matching tables are replaced. The script reports missing CSV files; check its output before building facts.
2. **`build_facts.py` — analytical transformation.** Recreates four denormalized fact tables using source-table joins and timestamp casts. Run after ingestion and whenever its SQL or underlying source data changes.

| Analytical table | Grain | Important attributes |
| --- | --- | --- |
| `fact_orders` | One row per order | Order status, `customer_unique_id`, buyer geography, purchase/delivery/estimated timestamps, delivery days. |
| `fact_order_items` | One row per order item | Product/category, seller and seller geography, buyer state, product price, freight billed, purchase timestamp. |
| `fact_payments` | One row per payment record | Payment type, installment count, payment amount, order and buyer attributes. |
| `fact_reviews` | One row per review record | Score, review text, review dates, order and buyer attributes. |

Order, item, payment, and review tables have **different grains**. Metrics aggregate at the appropriate grain rather than joining all facts into one rowset, which would multiply amounts and counts for multi-item or multi-payment orders.

## Project structure

```text
olist-dashboard/
├── app.py                     # Streamlit entry point and tab navigation
├── ingest.py                  # Kaggle CSV -> DuckDB source tables
├── build_facts.py             # Source tables -> analytical fact tables
├── requirements.txt
├── core/
│   ├── database.py            # Cached read-only DuckDB connection
│   ├── filters.py             # Parameterized global business filters
│   ├── styles.py              # Shared dashboard CSS
│   └── metrics/
│       ├── financial.py       # Product sales, baskets, payments, regions
│       ├── operations.py      # Delivery SLA and freight metrics
│       ├── customer.py        # Reviews and delivery/rating analysis
│       ├── seller.py          # Seller performance and segmentation
│       └── time_intelligence.py # Historical calendar-period analysis
└── tabs/
    ├── executive.py
    ├── revenue.py
    ├── operations.py
    ├── customer.py
    ├── seller.py
    ├── time_intelligence.py
    └── explorer.py
```

## Data dictionary — dashboard metrics

Unless stated otherwise, financial amounts are **BRL (R$)**, sales mean **product gross merchandise value (GMV)** from `fact_order_items.price` (excluding freight, refunds, and platform commissions), and metrics respect the selected order-status and buyer-state filters. `COUNT(*)` on `fact_order_items` counts item records; order-level measures use `fact_orders`.

### Sales and order volume

| Metric | Description | Formula / source | Business purpose |
| --- | --- | --- | --- |
| Total Sales / Product GMV | Product price value for selected transactions; not platform revenue. | `SUM(fact_order_items.price)` | Track marketplace product-sales volume. |
| Total Orders | Orders matching global filters, including orders without item records. | `COUNT(*)` on `fact_orders` | Track transaction volume. |
| Total Items Sold | Order-item records in the selected orders; not proof of dispatch. | `COUNT(*)` on `fact_order_items` | Measure item volume. |
| Average Order Value (AOV) | Product GMV per selected order. | Total Sales / Total Orders | Understand average order spend. |
| Unique Customers | Distinct Olist buyer identities across selected orders. | `COUNT(DISTINCT fact_orders.customer_unique_id)` | Avoid treating repeat orders as separate people. |
| Items per Order / Basket Size | Mean number of order-item records per order. | Total Items Sold / Total Orders | Monitor basket composition. |
| Sales per Unique Customer | Average product GMV per observed buyer, **not lifetime CLV**. | Total Sales / Unique Customers | Understand historical spend per buyer. |
| Monthly Product GMV | Product sales grouped by purchase month. | `SUM(price) GROUP BY STRFTIME(purchase_timestamp, '%Y-%m')` | Show seasonality and sales trend. |
| Top Product Categories | Ten categories with highest selected product GMV. | `SUM(price)` by `product_category`, descending, top 10 | Identify leading product categories. |
| Top Buyer States by GMV | Ten buyer states with the highest product GMV; includes distinct order count. | `SUM(price)` and `COUNT(DISTINCT order_id)` by `customer_state` | Understand geographic demand. |

### Revenue and payments

| Metric | Description | Formula / source | Business purpose |
| --- | --- | --- | --- |
| Freight Charged | Shipping amount recorded on order items; **not verified carrier expense**. | `SUM(fact_order_items.freight_value)` | Quantify customer-billed freight. |
| Freight-to-Sales Ratio | Freight billed relative to product GMV. | Freight Charged / Total Sales | Compare shipping charges with merchandise value. |
| Sales Less Freight (Illustrative) | Arithmetic difference, **not accounting gross profit**; product costs, seller payouts, and actual logistics expenses are unavailable. | Total Sales − Freight Charged | Illustrate the size of recorded freight relative to product sales. |
| Payment Method Value | Total recorded payment amount by payment type; may include freight and other payment components. | `SUM(fact_payments.payment_value)` by `payment_type` | Analyze payment-method mix. |
| Orders by Payment Method | Distinct orders using each payment method; an order may appear in multiple methods. | `COUNT(DISTINCT order_id)` by `payment_type` | Understand payment adoption. |
| Installment Distribution | Distinct orders by positive installment count, displaying the first 12 counts. | `COUNT(DISTINCT order_id)` by `payment_installments > 0` | Understand financing behavior. |

### Operations and delivery

| Metric | Description | Formula / source | Business purpose |
| --- | --- | --- | --- |
| Average Delivery Days | Average calendar-day difference between purchase and actual delivery for orders with a delivery timestamp. | `AVG(fact_orders.delivery_days)` for delivered-timestamp rows | Monitor customer delivery lead time. |
| Delivered Orders | Selected orders with an actual delivery timestamp. | `COUNT(*) WHERE delivered_timestamp IS NOT NULL` | Define delivered-order volume. |
| Delayed Delivered Orders % | Late orders among delivered orders with a valid estimated delivery timestamp. | `100 × COUNT(delivered_timestamp > estimated_delivery_timestamp) / COUNT(delivered orders with estimate)` | Monitor delivery SLA adherence without counting undelivered orders as on-time. |
| Fulfilled Items (Delivered Orders) | Item records whose order status is `delivered`; **proxy**, not proof of warehouse dispatch. | `COUNT(*)` on items where `order_status = 'delivered'` | Approximate fulfilled item volume. |
| Average Freight Charged per Item | Average recorded freight charge across selected item records. | `AVG(fact_order_items.freight_value)` | Compare per-item freight burden. |
| Regional Freight vs Product Price | Average item freight and product price grouped by buyer state. | `AVG(freight_value)` and `AVG(price)` by `customer_state` | Examine regional differences in shipping charges. |

### Customer experience

| Metric | Description | Formula / source | Business purpose |
| --- | --- | --- | --- |
| Total Reviews | Review records linked to selected orders. | `COUNT(*)` on filtered `fact_reviews` | Measure feedback volume. |
| Average Review Score | Mean score of selected reviews on a 1–5 scale. | `AVG(review_score)` | Track observed satisfaction. |
| Positive Reviews % | Share of review records with scores of 4 or 5. | `100 × COUNT(review_score >= 4) / Total Reviews` | Track favorable feedback. |
| Review Score Distribution | Number of reviews at each score. | `COUNT(*) GROUP BY review_score` | Show rating mix beyond the mean. |
| Delivery Timeliness vs Rating | Average review score and review count for late versus on-time delivered orders with estimates. | Classify `delivered_timestamp > estimated_delivery_timestamp`; then `AVG(review_score)` and `COUNT(*)` | Explore association between delivery experience and ratings; not a causal estimate. |

### Marketplace and sellers

| Metric | Description | Formula / source | Business purpose |
| --- | --- | --- | --- |
| Active Sellers | Distinct non-null sellers with selected item sales. | `COUNT(DISTINCT seller_id)` on filtered `fact_order_items` | Track participating sellers. |
| Seller-Attributed GMV | Product GMV associated with non-null seller IDs. | `SUM(price)` for items with `seller_id IS NOT NULL` | Define seller-analysis revenue base. |
| Average Sales per Seller | Mean seller-attributed product GMV per active seller. | Seller-Attributed GMV / Active Sellers | Compare seller productivity. |
| Top 10 Seller GMV Share | Share of seller-attributed GMV generated by the ten highest-GMV sellers. | Top 10 sellers' `SUM(price)` / Seller-Attributed GMV | Monitor marketplace concentration. |
| Largest Seller GMV Share | Share generated by the single highest-GMV seller. | `MAX(seller GMV)` / Seller-Attributed GMV | Monitor reliance on the leading seller. |
| Sales by Seller Segment | Product GMV by **dynamic seller-count quartile**, ranked by seller GMV within current filters. These are not official seller classes. | Aggregate seller `SUM(price)`; assign `NTILE(4) OVER (ORDER BY sales DESC, seller_id)`; sum by quartile | Compare contribution from higher- and lower-volume sellers. |
| Top Sellers | Ten highest-GMV sellers, with item and per-seller distinct-order counts. | `SUM(price)`, `COUNT(*)`, `COUNT(DISTINCT order_id)` by seller | Identify leading sellers. |
| Seller Geography | GMV, distinct sellers, and distinct orders by **seller** state; global state filter still selects **buyer** state. | Aggregate selected items by `seller_state` | Understand seller-location distribution. |

Seller-level order counts are **not additive across sellers**: one multi-seller order can appear in multiple seller totals.

### Historical time intelligence

All periods use `fact_order_items.purchase_timestamp` and an adjustable **reporting as-of date**, which defaults to the latest purchase date available under the selected filters. The historical dataset is not a live sales feed. Dates are inclusive; Feb 29 maps to Feb 28 for prior-year comparisons.

| Metric | Description | Formula / source | Business purpose |
| --- | --- | --- | --- |
| Sales MTD | Product GMV from the first of the as-of month through the as-of date. | `SUM(price)` within `[month_start, as_of]` | Assess month-to-date sales. |
| Sales LY (Same MTD) | Product GMV in the aligned prior-year month-to-date window. | `SUM(price)` within `[prior_year_month_start, prior_year_as_of]` | Provide a comparable MTD baseline. |
| MTD YoY Growth | Relative change from the aligned prior-year MTD period. | `(Sales MTD / Sales LY Same MTD) − 1` | Measure like-for-like monthly growth. |
| Sales YTD | Product GMV from Jan 1 through the as-of date. | `SUM(price)` within `[year_start, as_of]` | Track year-to-date sales. |
| Sales LY (Same YTD) | Product GMV in the aligned prior-year YTD window. | `SUM(price)` within `[prior_year_Jan_1, prior_year_as_of]` | Provide a comparable annual baseline. |
| YTD YoY Growth | Relative change from the aligned prior-year YTD period. | `(Sales YTD / Sales LY Same YTD) − 1` | Measure year-to-date growth. |
| Monthly GMV Comparison | Calendar-month GMV for the selected and preceding year; selected as-of month may be incomplete. | `SUM(price)` by purchase year and month | Visualize seasonality; use aligned MTD KPIs for partial-month comparisons. |

Prior-year KPIs display **N/A** if the filtered data's earliest/latest observed dates do not span the entire comparison window or if the previous-period denominator is zero. This date-range check does **not** establish that every day in the interval has observations.

## Metric interpretation and validation

- The dashboard reports **product GMV**, not recognized revenue, net sales, contribution margin, or gross profit. Payment amounts and product GMV are different measures and should not be expected to match.
- Fact-table measures are aggregated at their intended grain. Cross-tab totals may differ when a metric excludes null seller IDs, requires a delivery timestamp, or applies a different eligibility rule.
- The project uses parameterized DuckDB `?` placeholders for business filters. The Data Explorer's CSV and table exploration is independent of the global business filters.
- **End-to-end execution and reconciliation against the full Olist dataset remain pending.** For a quick syntax check, run:

```bash
python -m compileall -q app.py ingest.py build_facts.py core tabs
```

Validate KPI values against independent DuckDB queries before using them for business decisions.
