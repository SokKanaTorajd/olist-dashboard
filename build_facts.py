"""Build order-, item-, payment- and review-grain analytical fact tables.

Run after ingest.py. Rebuilds the four fact tables on every run.
"""
from pathlib import Path
import duckdb

DB_PATH = Path(__file__).resolve().parent / 'olist.duckdb'
if not DB_PATH.exists():
    raise FileNotFoundError('olist.duckdb not found. Run python ingest.py first.')

with duckdb.connect(str(DB_PATH)) as con:
    print('Building Olist analytical fact tables...')
    con.execute('''CREATE OR REPLACE TABLE fact_orders AS
        SELECT o.order_id, o.customer_id, c.customer_unique_id,
            c.customer_state, c.customer_city, o.order_status,
            TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchase_timestamp,
            TRY_CAST(o.order_delivered_customer_date AS TIMESTAMP) AS delivered_timestamp,
            TRY_CAST(o.order_estimated_delivery_date AS TIMESTAMP) AS estimated_delivery_timestamp,
            DATE_DIFF('day', TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP),
                      TRY_CAST(o.order_delivered_customer_date AS TIMESTAMP)) AS delivery_days
        FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id''')
    con.execute('''CREATE OR REPLACE TABLE fact_order_items AS
        SELECT i.order_id, i.order_item_id, i.product_id, i.seller_id,
            o.customer_id, c.customer_state,
            COALESCE(t.product_category_name_english,p.product_category_name) AS product_category,
            s.seller_state, s.seller_city,
            i.price, i.freight_value, o.order_status,
            TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchase_timestamp
        FROM order_items i JOIN orders o ON i.order_id=o.order_id
        LEFT JOIN customers c ON o.customer_id=c.customer_id
        LEFT JOIN sellers s ON i.seller_id=s.seller_id
        LEFT JOIN products p ON i.product_id=p.product_id
        LEFT JOIN product_category_translation t
            ON p.product_category_name=t.product_category_name''')
    con.execute('''CREATE OR REPLACE TABLE fact_payments AS
        SELECT p.order_id,p.payment_sequential,p.payment_type,p.payment_installments,
            p.payment_value,o.customer_id,c.customer_state,
            TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchase_timestamp
        FROM order_payments p JOIN orders o ON p.order_id=o.order_id
        LEFT JOIN customers c ON o.customer_id=c.customer_id''')
    con.execute('''CREATE OR REPLACE TABLE fact_reviews AS
        SELECT r.review_id,r.order_id,r.review_score,r.review_comment_title,
            r.review_comment_message,
            TRY_CAST(r.review_creation_date AS TIMESTAMP) AS review_creation_date,
            TRY_CAST(r.review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp,
            o.customer_id,c.customer_state,
            TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchase_timestamp
        FROM reviews r JOIN orders o ON r.order_id=o.order_id
        LEFT JOIN customers c ON o.customer_id=c.customer_id''')
print('Four fact tables built successfully.')
