"""Review-grain satisfaction metrics; order-grain delivery classification."""

def review_kpis(con, filters):
    """Return review count, mean rating, and share of reviews scoring at least four."""
    where, params = filters.where('o')
    row = con.execute(f'''SELECT ROUND(AVG(r.review_score),2) AS avg_score,
        COUNT(*) AS total_reviews,
        COUNT(*) FILTER (WHERE r.review_score >= 4) AS positive_reviews
        FROM fact_reviews r JOIN fact_orders o USING(order_id) {where}''', params).fetchone()
    avg, total, positive = row
    return dict(avg_score=avg, total_reviews=total, positive_reviews=positive,
                positive_pct=100 * positive / total if total else None)


def review_distribution(con, filters):
    """Count review records by rating within selected orders."""
    where, params = filters.where('o')
    return con.execute(f'''SELECT r.review_score, COUNT(*) AS count
        FROM fact_reviews r JOIN fact_orders o USING(order_id) {where}
        GROUP BY 1 ORDER BY 1 DESC''', params).df()


def delivery_vs_rating(con, filters):
    """Compare reviews for late and on-time delivered orders with estimates."""
    where, params = filters.where('o')
    return con.execute(f'''SELECT CASE WHEN o.delivered_timestamp > o.estimated_delivery_timestamp
            THEN 'Late Delivery' ELSE 'On-Time Delivery' END AS delivery_status,
        ROUND(AVG(r.review_score),2) AS avg_rating,
        COUNT(*) AS total_reviews
        FROM fact_reviews r JOIN fact_orders o USING(order_id)
        {where} AND o.delivered_timestamp IS NOT NULL
        AND o.estimated_delivery_timestamp IS NOT NULL
        GROUP BY 1''', params).df()
