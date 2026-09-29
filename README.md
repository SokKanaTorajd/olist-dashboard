# Olist E-Commerce Analytics Dashboard — Phase 1

Streamlit + DuckDB analytics for the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

## Setup

1. Download the Kaggle CSVs and put them in the directory expected by your existing `ingest.py` (keep your existing ingest script; it is not included in this update).
2. Install dependencies: `pip install streamlit duckdb pandas plotly`.
3. From the project root, run `python ingest.py`, then `python build_facts.py`, then `streamlit run app.py`.
4. Copy this package's `app.py`, `build_facts.py`, `core/`, and four business tabs into your project. Keep your existing `tabs/explorer.py` if customized; a copy is included for convenience.

`build_facts.py` rebuilds all four fact tables. Run it while the Streamlit application is stopped so the DuckDB file is not held open by its read-only connection.

## Structure

- `core/filters.py`: parameterized order status and customer state filters.
- `core/metrics/financial.py`: product sales, AOV, basket size, freight, payments and region/category trends.
- `core/metrics/operations.py`: order-grain delivery SLAs and item-grain freight.
- `core/metrics/customer.py`: review KPIs and delivery impact.
- `tabs/`: Streamlit presentation layer. `explorer.py` keeps its independent data-source filters.

## Metric definitions and limitations

- **Total Sales (GMV)**: sum of `fact_order_items.price` for selected orders; excludes shipping and refunds. It is product sales, **not** Olist's own recognized revenue.
- **Total Orders**: count of matching `fact_orders` records, including orders without item records. Default status is `delivered`.
- **Total Items Sold**: count of matching order-item records; **Fulfilled Items** counts those with `order_status = 'delivered'` (delivery status is a proxy, not warehouse dispatch proof).
- **AOV**: product sales / matching orders. An order with no item records remains in the denominator.
- **Sales per Unique Customer**: product sales / distinct `customers.customer_unique_id`. This is **not** lifetime customer value; historical snapshot only.
- **Freight Charged**: sum of `order_items.freight_value`; freight billed, not the actual platform-incurred shipping expense.
- **Sales Less Freight**: illustrative arithmetic only, **not gross profit**. The dataset lacks product cost, seller payout, actual carrier cost, returns and fee accounting.
- **Delayed Orders %**: late delivered orders / delivered orders with a non-null estimated delivery timestamp; computed at the order grain.
- **Average Delivery Days**: mean of `DATE_DIFF('day', purchase_timestamp, delivered_timestamp)` for delivered orders; whole-day boundaries, not elapsed hours / 24.
- **Positive Reviews %**: reviews with score >= 4 / all reviews, at review grain; not a unique-customer satisfaction rate.
- The default state filter now includes **all states** rather than the first five alphabetically. Clear a filter to select all values, preserving the previous empty-selection behavior.
- `fact_orders.customer_unique_id` requires rebuilding the facts with the included script.

## Validation

Run `python -m compileall -q app.py build_facts.py core tabs` to check Python syntax. Compare outputs with your manual DuckDB queries before treating the dashboard as validated. The SQL uses DuckDB `?` parameters instead of interpolating selected filter values.
