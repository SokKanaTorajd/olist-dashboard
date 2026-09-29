# Olist E-Commerce Analytics Dashboard — Phase 2

Streamlit + DuckDB analytics for the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

## Setup

1. Download the Kaggle CSVs and put them in the directory expected by your existing `ingest.py` (keep your existing ingest script; it is not included in this update).
2. Install dependencies: `pip install streamlit duckdb pandas plotly`.
3. From the project root, run `python ingest.py`, then `python build_facts.py`, then `streamlit run app.py`.
4. Copy this package's `app.py`, `build_facts.py`, `core/`, and five business tabs into your project. Keep your existing `tabs/explorer.py` if customized; a copy is included for convenience.

`build_facts.py` rebuilds all four fact tables. Run it while the Streamlit application is stopped so the DuckDB file is not held open by its read-only connection.

## Phase 2: Marketplace & Seller Analytics

- Added **Marketplace & Sellers** tab with active sellers, average product GMV per seller, top-10 seller concentration, highest seller concentration, top seller ranking and seller-state sales.
- **Seller segments** are dynamically recalculated product-GMV quartiles under the current order-status and buyer-state filters; they are not supplied business classifications. A segment contains roughly one-quarter of the filtered active sellers, not one-quarter of GMV.
- `fact_order_items` now includes `seller_state` and `seller_city` from the original `sellers` table. Rebuild facts after copying this release.
- Top-10 seller share = GMV from the ten largest sellers / total seller-attributed GMV. Average sales per seller = seller-attributed GMV / active sellers.
- Buyer-state global filters remain based on **customer_state**; seller-state charts show **seller_state**.
- This phase adds no `dim_seller` or external seller classification. If an official segment mapping becomes available, replace the derived quartiles.
- No end-to-end database validation has been performed; follow up with manual SQL comparisons after Phase 3.

## Structure

- `core/filters.py`: parameterized order status and customer state filters.
- `core/metrics/financial.py`: product sales, AOV, basket size, freight, payments and region/category trends.
- `core/metrics/operations.py`: order-grain delivery SLAs and item-grain freight.
- `core/metrics/customer.py`: review KPIs and delivery impact.
- `core/metrics/seller.py`: seller ranking, dynamic quartiles, concentration and geography.
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

## Phase 3: Historical Time Intelligence

- Added **Time Intelligence** tab and `core/metrics/time_intelligence.py` with Sales MTD, same-period-last-year MTD, MTD YoY growth, Sales YTD, same-period-last-year YTD, YTD YoY growth, and monthly GMV comparison.
- Reporting **as-of date** defaults to the latest purchase date in the currently filtered `fact_order_items`, not today's date. Choose an earlier date in the tab to explore historical snapshots.
- Product GMV is `SUM(fact_order_items.price)`, filtered by global order status and buyer state, and attributed to the **purchase date**. It excludes freight and refunds and is not Olist's recognized platform revenue.
- LY compares the same calendar start/end dates in the prior year (Feb 29 maps to Feb 28). Growth is unavailable (`N/A`) if the prior-year comparison window is outside the filtered dataset's observed date range or if prior-year sales are zero. Coverage by min/max dates is not proof that every intervening date has records.
- The monthly chart shows calendar-month aggregates for the selected and prior year. The current as-of month can be partial; **use MTD KPIs, not the monthly chart, for aligned same-period growth**.
- No fact-table schema change is needed for Phase 3. Keep Phase 2's `build_facts.py` and existing fact tables; no rebuild is required if Phase 2 is already installed.
- This release has static validation only. Manual SQL comparisons and end-to-end testing are deferred until all phases are implemented.

### Branch workflow

```bash
git switch dev
git pull origin dev
git switch -c feature/time-intelligence
# Copy the updated Phase 3 files, then:
git add app.py core/metrics/time_intelligence.py tabs/time_intelligence.py README.md
git commit -m "feat(analytics): add historical sales time intelligence"
git push -u origin feature/time-intelligence
```

Open a PR from `feature/time-intelligence` into `dev`. After manual validation, merge `dev` into `main` through a separate PR.
