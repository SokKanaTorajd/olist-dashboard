"""Order-grain delivery SLAs and item-grain shipping measures."""

def delivery_kpis(con, filters):
    where, params = filters.where('o')
    row = con.execute(f'''SELECT ROUND(AVG(delivery_days),1) AS avg_delivery_days,
        COUNT(*) AS delivered_orders,
        COUNT(*) FILTER (WHERE estimated_delivery_timestamp IS NOT NULL) AS eligible_orders,
        COUNT(*) FILTER (WHERE estimated_delivery_timestamp IS NOT NULL
            AND delivered_timestamp > estimated_delivery_timestamp) AS late_orders
        FROM fact_orders o {where} AND delivered_timestamp IS NOT NULL''', params).fetchone()
    avg_days, delivered, eligible, late = row
    return dict(avg_delivery_days=avg_days, delivered_orders=delivered,
                eligible_orders=eligible, late_orders=late,
                delayed_pct=100 * late / eligible if eligible else None)


def item_kpis(con, filters):
    where, params = filters.where('f')
    row = con.execute(f'''SELECT ROUND(AVG(f.freight_value),2) AS avg_freight,
        COUNT(*) FILTER (WHERE f.order_status='delivered') AS fulfilled_items
        FROM fact_order_items f {where}''', params).fetchone()
    return dict(avg_freight=row[0], fulfilled_items=row[1])


def regional_freight(con, filters):
    where, params = filters.where('f')
    return con.execute(f'''SELECT f.customer_state,
        ROUND(AVG(f.price),2) AS avg_product_price,
        ROUND(AVG(f.freight_value),2) AS avg_freight
        FROM fact_order_items f {where}
        GROUP BY 1 ORDER BY avg_freight DESC''', params).df()
