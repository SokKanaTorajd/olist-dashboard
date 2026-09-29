import streamlit as st
import plotly.express as px
from core.metrics import financial


def render(con, filters):
    st.subheader('Payment & Regional Analysis')
    k = financial.overview(con, filters)
    a, b, c = st.columns(3)
    a.metric('Product Sales (GMV)', f"R$ {k['total_sales']:,.2f}")
    b.metric('Freight Charged', f"R$ {k['freight_value']:,.2f}",
             help='Freight billed on order items; not verified carrier expense.')
    c.metric('Freight-to-Sales Ratio', f"{k['freight_to_sales']:.1%}")
    a, b = st.columns(2)
    a.metric('Sales Less Freight (Illustrative)', f"R$ {k['sales_less_freight']:,.2f}",
             help='Not gross profit: product costs, seller payouts and actual logistics expenses are unknown.')
    b.metric('Sales per Unique Customer', f"R$ {k['sales_per_customer']:,.2f}")
    st.caption('Freight is the shipping amount recorded on order items. '
               'Sales less freight is illustrative, not accounting gross profit.')
    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown('### 💳 Payment Methods Breakdown')
        df = financial.payment_methods(con, filters)
        st.plotly_chart(px.pie(df, names='payment_type', values='total_value',
                               hole=.4, title='Share of Payment Volume (BRL)'),
                        use_container_width=True)
    with right:
        st.markdown('### 🔢 Installments Distribution')
        df = financial.installments(con, filters)
        st.plotly_chart(px.bar(df, x='payment_installments', y='total_orders',
                               labels={'payment_installments':'Installment Count (x)',
                                       'total_orders':'Orders'}), use_container_width=True)
    st.markdown('### 📍 Top States by Sales Concentration')
    df = financial.regional_sales(con, filters)
    st.plotly_chart(px.bar(df, x='customer_state', y='gmv', color='total_orders',
                           labels={'gmv':'GMV (BRL)','customer_state':'State'}),
                    use_container_width=True)
