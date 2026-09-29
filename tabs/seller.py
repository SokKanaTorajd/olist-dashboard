"""Marketplace & Seller Analytics dashboard."""
import plotly.express as px
import streamlit as st
from core.metrics import seller


def render(con, filters):
    st.subheader('Marketplace & Seller Analytics')
    st.caption('Seller performance reflects the selected order statuses and customer regions. '
               'Sales represent product GMV, not Olist platform revenue.')
    k = seller.seller_kpis(con, filters)
    concentration = seller.concentration(con, filters)
    a, b, c, d = st.columns(4)
    a.metric('Active Sellers', f"{k['active_sellers']:,}")
    b.metric('Average Sales per Seller', f"R$ {k['avg_sales_per_seller']:,.2f}")
    c.metric('Top 10 Seller GMV Share', f'{concentration:.1%}')
    d.metric('Largest Seller GMV Share', f"{k['largest_seller_share']:.1%}")
    st.divider()

    st.markdown('### Seller Segments by Product GMV')
    st.caption('Dynamic quartiles: sellers are ranked by GMV within the current filters '
               'and split into four roughly equal-sized groups. These are analytical '
               'segments, not official Olist seller classifications.')
    segments = seller.seller_segments(con, filters)
    if segments.empty:
        st.info('No seller sales match the current filters.')
    else:
        left, right = st.columns(2)
        with left:
            fig = px.bar(segments, x='segment', y='sales', text='sellers',
                         labels={'sales': 'Product GMV (BRL)', 'segment': 'Seller segment'},
                         title='Sales by Seller Segment')
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = px.pie(segments, names='segment', values='sales', hole=.45,
                         title='Seller Segment GMV Share')
            st.plotly_chart(fig, use_container_width=True)
        with st.expander('Seller segment details'):
            st.dataframe(segments.drop(columns=['tier']), use_container_width=True,
                         hide_index=True)
            st.caption('Seller order counts are summed across sellers; a multi-seller order '
                       'can appear in multiple seller counts.')

    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown('### Top 10 Sellers by Product GMV')
        top = seller.top_sellers(con, filters)
        if top.empty:
            st.info('No sellers match the current filters.')
        else:
            fig = px.bar(top.sort_values('sales'), x='sales', y='seller_id',
                         orientation='h', hover_data=['seller_state','orders','items'],
                         labels={'sales':'Product GMV (BRL)','seller_id':'Seller ID'})
            fig.update_layout(yaxis={'type':'category'})
            st.plotly_chart(fig, use_container_width=True)
            with st.expander('Top seller details'):
                st.dataframe(top, use_container_width=True, hide_index=True)
    with right:
        st.markdown('### Seller Location by State')
        geo = seller.seller_geography(con, filters)
        if geo.empty:
            st.info('No seller locations match the current filters.')
        else:
            fig = px.bar(geo, x='seller_state', y='sales', color='active_sellers',
                         labels={'seller_state':'Seller state', 'sales':'Product GMV (BRL)',
                                 'active_sellers':'Active sellers'})
            st.plotly_chart(fig, use_container_width=True)
            st.caption('Seller state is the seller location, not the buyer state '
                       'used by the global region filter.')
