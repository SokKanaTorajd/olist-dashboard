"""Product GMV, order volume, payment mix, and buyer-region analytics.

Product sales exclude freight; payment values can include additional charges.
The order and item facts are aggregated separately to prevent fan-out.
"""

def overview(con, filters):
    """Return shared order- and item-grain KPIs under global filters."""
    order_where, op = filters.where('o')
    item_where, ip = filters.where('f')
    orders = con.execute(f'''SELECT COUNT(*) AS total_orders,
        COUNT(DISTINCT customer_unique_id) AS unique_customers
        FROM fact_orders o {order_where}''', op).fetchone()
    items = con.execute(f'''SELECT COALESCE(SUM(price),0) AS total_sales,
        COUNT(*) AS total_items, COALESCE(SUM(freight_value),0) AS freight_value,
        COUNT(DISTINCT seller_id) AS active_sellers
        FROM fact_order_items f {item_where}''', ip).fetchone()
    sales, count_items, freight, sellers = items
    count_orders, customers = orders
    return dict(total_sales=sales, total_orders=count_orders,
                total_items=count_items, unique_customers=customers,
                aov=sales / count_orders if count_orders else 0,
                basket_size=count_items / count_orders if count_orders else 0,
                sales_per_customer=sales / customers if customers else 0,
                freight_value=freight,
                freight_to_sales=freight / sales if sales else 0,
                sales_less_freight=sales - freight,
                active_sellers=sellers)


def monthly_sales(con, filters):
    """Aggregate product GMV by order purchase month."""
    where, params = filters.where('f')
    return con.execute(f'''SELECT STRFTIME(purchase_timestamp,'%Y-%m') AS month,
        ROUND(SUM(price),2) AS gmv FROM fact_order_items f {where}
        GROUP BY 1 ORDER BY 1''', params).df()


def top_categories(con, filters):
    """Return the ten product categories with highest filtered GMV."""
    where, params = filters.where('f')
    return con.execute(f'''SELECT COALESCE(product_category,'Unknown') AS category,
        ROUND(SUM(price),2) AS total_gmv FROM fact_order_items f {where}
        GROUP BY 1 ORDER BY total_gmv DESC LIMIT 10''', params).df()


def payment_methods(con, filters):
    """Aggregate payment value and distinct orders by payment type."""
    where, params = filters.where('o')
    return con.execute(f'''SELECT p.payment_type,
        COUNT(DISTINCT p.order_id) AS total_orders,
        ROUND(SUM(p.payment_value),2) AS total_value
        FROM fact_payments p JOIN fact_orders o USING(order_id)
        {where} GROUP BY 1 ORDER BY total_value DESC''', params).df()


def installments(con, filters):
    """Count distinct orders by positive installment count."""
    where, params = filters.where('o')
    return con.execute(f'''SELECT p.payment_installments,
        COUNT(DISTINCT p.order_id) AS total_orders
        FROM fact_payments p JOIN fact_orders o USING(order_id)
        {where} AND p.payment_installments > 0
        GROUP BY 1 ORDER BY 1 LIMIT 12''', params).df()


def regional_sales(con, filters):
    """Rank buyer states by product GMV and distinct orders."""
    where, params = filters.where('f')
    return con.execute(f'''SELECT f.customer_state,
        COUNT(DISTINCT f.order_id) AS total_orders,
        ROUND(SUM(f.price),2) AS gmv
        FROM fact_order_items f {where}
        GROUP BY 1 ORDER BY gmv DESC LIMIT 10''', params).df()
