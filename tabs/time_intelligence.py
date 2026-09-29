"""Historical product-sales time intelligence dashboard."""
from datetime import date
import calendar
import streamlit as st
import plotly.express as px
from core.metrics import time_intelligence as ti


def _currency(value):
    return 'N/A' if value is None else f'R$ {value:,.2f}'


def _percent(value):
    return 'N/A' if value is None else f'{value:+.1%}'


def render(con, filters):
    st.subheader('Historical Sales & Time Intelligence')
    first, last = ti.available_dates(con, filters)
    if first is None:
        st.info('No product sales found for the selected global filters.')
        return

    st.caption(f'Available filtered purchase dates: {first:%d %b %Y} – {last:%d %b %Y}. '
               'This is historical data, not live sales.')
    as_of = st.date_input('Reporting as-of date', value=last, min_value=first,
                          max_value=last, key='time_as_of',
                          help='Month-to-date and year-to-date end on this date, inclusive.')
    if not isinstance(as_of, date):
        st.warning('Select a single reporting date.')
        return
    k = ti.period_kpis(con, filters, as_of)

    st.markdown('### Period KPIs')
    a, b, c = st.columns(3)
    a.metric('Sales MTD', _currency(k['mtd']),
             help=f"Product GMV from {k['mtd_start']:%d %b %Y} to {as_of:%d %b %Y}.")
    b.metric('Sales LY (same MTD)', _currency(k['ly_mtd']),
             help=f"Comparable prior-year period: {k['ly_mtd_start']:%d %b %Y} – {k['ly_as_of']:%d %b %Y}.")
    c.metric('MTD YoY Growth', _percent(k['mtd_yoy']),
             help='(Current MTD / same prior-year MTD) − 1. N/A if prior-year coverage is missing or sales are zero.')

    d, e, f = st.columns(3)
    d.metric('Sales YTD', _currency(k['ytd']))
    e.metric('Sales LY (same YTD)', _currency(k['ly_ytd']))
    f.metric('YTD YoY Growth', _percent(k['ytd_yoy']))
    if k['ly_mtd'] is None or k['ly_ytd'] is None:
        st.info('One or more prior-year comparisons are unavailable because the selected '
                'filters do not have observations covering the full comparison window.')

    st.divider()
    st.markdown('### Monthly GMV: selected year vs previous year')
    year = as_of.year
    df = ti.monthly_comparison(con, filters, year, as_of)
    if df.empty:
        st.info('No monthly sales available.')
        return
    df['month'] = df['month_number'].map(lambda m: calendar.month_abbr[int(m)])
    df['year'] = df['sales_year'].astype(str)
    fig = px.line(df, x='month', y='gmv', color='year', markers=True,
                  category_orders={'month': list(calendar.month_abbr)[1:]},
                  labels={'gmv': 'Product GMV (BRL)', 'month': 'Purchase month', 'year': 'Year'})
    st.plotly_chart(fig, use_container_width=True)
    st.caption('The selected as-of month may be incomplete, while previous-year months are full calendar months. '
               'Use the MTD-aligned KPIs above for like-for-like growth comparisons.')
