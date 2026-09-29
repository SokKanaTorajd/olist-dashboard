"""Customer satisfaction and delivery-versus-rating dashboard."""

import streamlit as st
import plotly.express as px
from core.metrics import customer


def render(con, filters):
    st.subheader('Customer Reviews & Satisfaction Impact')
    k = customer.review_kpis(con, filters)
    a, b, c = st.columns(3)
    a.metric('Average Review Score', f"⭐ {k['avg_score']}/5.0" if k['avg_score'] is not None else 'N/A')
    b.metric('Total Reviews Analyzed', f"{k['total_reviews']:,}")
    c.metric('Positive Reviews (4–5 Stars)', f"{k['positive_pct']:.1f}%" if k['positive_pct'] is not None else 'N/A')
    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown('### ⭐ Review Score Distribution')
        df = customer.review_distribution(con, filters)
        st.plotly_chart(px.bar(df, x='review_score', y='count', color='review_score',
                               color_continuous_scale='RdYlGn'), use_container_width=True)
    with right:
        st.markdown('### ⚠️ Impact of Late Delivery on Ratings')
        df = customer.delivery_vs_rating(con, filters)
        st.plotly_chart(px.bar(df, x='delivery_status', y='avg_rating',
                               color='delivery_status', text='avg_rating'),
                        use_container_width=True)
