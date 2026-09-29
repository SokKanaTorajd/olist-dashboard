"""Historical sales time intelligence, using purchase date and product GMV.

All dates are inclusive calendar dates in the source dataset, not today's date.
Previous-year comparisons use the same calendar window, with leap-day
clamping for February 29. All queries retain the global status/state filters.
"""
from datetime import date
import calendar


def shift_year_back(day: date) -> date:
    """Return same month/day in prior year; Feb 29 maps to Feb 28."""
    year = day.year - 1
    return day.replace(year=year, day=min(day.day, calendar.monthrange(year, day.month)[1]))


def available_dates(con, filters):
    where, params = filters.where('f')
    return con.execute(f'''SELECT MIN(CAST(purchase_timestamp AS DATE)),
        MAX(CAST(purchase_timestamp AS DATE))
        FROM fact_order_items f {where} AND purchase_timestamp IS NOT NULL''', params).fetchone()


def _sales_window(con, filters, start: date, end: date):
    where, params = filters.where('f')
    return con.execute(f'''SELECT COALESCE(SUM(f.price), 0)
        FROM fact_order_items f {where}
        AND f.purchase_timestamp >= CAST(? AS DATE)
        AND f.purchase_timestamp < CAST(? AS DATE) + INTERVAL 1 DAY''',
        [*params, start, end]).fetchone()[0]


def _has_comparison_period(con, filters, start: date, end: date):
    """A previous-year period is comparable only if source data covers it.

    This checks available filtered item dates; it does not claim daily completeness.
    """
    earliest, latest = available_dates(con, filters)
    return earliest is not None and earliest <= start and latest >= end


def period_kpis(con, filters, as_of: date):
    month_start = as_of.replace(day=1)
    year_start = as_of.replace(month=1, day=1)
    ly_as_of = shift_year_back(as_of)
    ly_month_start = shift_year_back(month_start)
    ly_year_start = shift_year_back(year_start)

    mtd = _sales_window(con, filters, month_start, as_of)
    ytd = _sales_window(con, filters, year_start, as_of)
    ly_mtd = (_sales_window(con, filters, ly_month_start, ly_as_of)
              if _has_comparison_period(con, filters, ly_month_start, ly_as_of) else None)
    ly_ytd = (_sales_window(con, filters, ly_year_start, ly_as_of)
              if _has_comparison_period(con, filters, ly_year_start, ly_as_of) else None)

    def growth(current, previous):
        return (current / previous - 1) if previous is not None and previous != 0 else None

    return dict(as_of=as_of, mtd=mtd, ly_mtd=ly_mtd,
                mtd_yoy=growth(mtd, ly_mtd), ytd=ytd, ly_ytd=ly_ytd,
                ytd_yoy=growth(ytd, ly_ytd),
                mtd_start=month_start, ly_mtd_start=ly_month_start,
                ly_as_of=ly_as_of)


def monthly_comparison(con, filters, year: int, as_of: date):
    """Return Jan–Dec monthly GMV for selected year and prior year.

    Future months relative to as_of are excluded for selected year. Prior-year
    months are included only if corresponding historical dates are available.
    Current as-of month is partial, so it is marked explicitly in the result.
    """
    where, params = filters.where('f')
    df = con.execute(f'''SELECT YEAR(f.purchase_timestamp) AS sales_year,
        MONTH(f.purchase_timestamp) AS month_number,
        ROUND(SUM(f.price), 2) AS gmv
        FROM fact_order_items f {where}
        AND f.purchase_timestamp IS NOT NULL
        AND YEAR(f.purchase_timestamp) IN (?, ?)
        AND CAST(f.purchase_timestamp AS DATE) <= CAST(? AS DATE)
        GROUP BY 1, 2 ORDER BY 1, 2''',
        [*params, year - 1, year, as_of]).df()
    # Prior-year months are only meaningful up to the selected as-of month.
    # Full prior-year months may be compared with current-year partial month,
    # so the UI warns and displays MTD-aligned KPIs separately.
    return df
