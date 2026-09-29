"""Seller analytics at seller/item grain; quartiles are dynamic for current filters."""


def seller_kpis(con, filters):
    where, params = filters.where('f')
    row = con.execute(f"""WITH seller_sales AS (
        SELECT f.seller_id, SUM(f.price) AS sales
        FROM fact_order_items f {where} AND f.seller_id IS NOT NULL
        GROUP BY 1
    )
    SELECT COUNT(*) AS active_sellers,
           COALESCE(SUM(sales),0) AS seller_attributed_sales,
           COALESCE(AVG(sales),0) AS avg_sales_per_seller,
           COALESCE(MAX(sales),0) AS largest_seller_sales
    FROM seller_sales""", params).fetchone()
    count, sales, average, largest = row
    return dict(active_sellers=count, seller_attributed_sales=sales,
                avg_sales_per_seller=average,
                largest_seller_share=largest / sales if sales else 0)


def top_sellers(con, filters, limit=10):
    where, params = filters.where('f')
    return con.execute(f"""SELECT f.seller_id,
        ANY_VALUE(f.seller_state) AS seller_state,
        COUNT(DISTINCT f.order_id) AS orders,
        COUNT(*) AS items,
        ROUND(SUM(f.price),2) AS sales
        FROM fact_order_items f {where} AND f.seller_id IS NOT NULL
        GROUP BY 1 ORDER BY sales DESC, f.seller_id LIMIT ?""",
        [*params, limit]).df()


def seller_segments(con, filters):
    """Rank sellers by filtered product sales; segment by seller count quartiles.

    NTILE distributes sellers into approximately equal-sized groups, not equal revenue.
    Small seller populations may have empty quartiles.
    """
    where, params = filters.where('f')
    return con.execute(f"""WITH seller_sales AS (
        SELECT f.seller_id, SUM(f.price) AS sales,
            COUNT(DISTINCT f.order_id) AS orders
        FROM fact_order_items f {where} AND f.seller_id IS NOT NULL
        GROUP BY 1
    ), ranked AS (
        SELECT *, NTILE(4) OVER (ORDER BY sales DESC, seller_id) AS tier
        FROM seller_sales
    )
    SELECT CASE tier WHEN 1 THEN 'Q1 · Highest sales'
                     WHEN 2 THEN 'Q2'
                     WHEN 3 THEN 'Q3'
                     ELSE 'Q4 · Lowest sales' END AS segment,
           tier, COUNT(*) AS sellers, SUM(orders) AS seller_order_counts,
           ROUND(SUM(sales),2) AS sales
    FROM ranked GROUP BY 1,2 ORDER BY tier""", params).df()


def seller_geography(con, filters, limit=10):
    where, params = filters.where('f')
    return con.execute(f"""SELECT COALESCE(f.seller_state,'Unknown') AS seller_state,
        COUNT(DISTINCT f.seller_id) AS active_sellers,
        COUNT(DISTINCT f.order_id) AS orders,
        ROUND(SUM(f.price),2) AS sales
        FROM fact_order_items f {where} AND f.seller_id IS NOT NULL
        GROUP BY 1 ORDER BY sales DESC LIMIT ?""", [*params, limit]).df()


def concentration(con, filters):
    """Top 10 seller share of seller-attributed sales, including tied order IDs once per seller."""
    where, params = filters.where('f')
    row = con.execute(f"""WITH seller_sales AS (
        SELECT f.seller_id, SUM(f.price) AS sales
        FROM fact_order_items f {where} AND f.seller_id IS NOT NULL
        GROUP BY 1
    ), ranked AS (
        SELECT sales, ROW_NUMBER() OVER (ORDER BY sales DESC, seller_id) AS rn
        FROM seller_sales
    )
    SELECT SUM(sales) FILTER (WHERE rn <= 10), SUM(sales) FROM ranked""", params).fetchone()
    top, total = row
    return (top or 0) / total if total else 0
