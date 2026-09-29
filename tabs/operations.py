import streamlit as st
import plotly.express as px
from core.metrics import financial, operations


def render(con, filters):
    st.subheader('Logistics Performance & Delivery SLA')
    d = operations.delivery_kpis(con, filters)
    i = operations.item_kpis(con, filters)
    f = financial.overview(con, filters)
    a, b, c = st.columns(3)
    a.metric('Avg Delivery Time', f"{d['avg_delivery_days']} Days" if d['avg_delivery_days'] is not None else 'N/A')
    b.metric('Avg Freight Charged per Item', f"R$ {i['avg_freight']:,.2f}" if i['avg_freight'] is not None else 'N/A')
    c.metric('Delayed Delivered Orders', f"{d['delayed_pct']:.2f}%" if d['delayed_pct'] is not None else 'N/A',
             help='Late deliveries / delivered orders with an estimated delivery timestamp.')
    a, b, c = st.columns(3)
    a.metric('Delivered Orders', f"{d['delivered_orders']:,}")
    b.metric('Fulfilled Items (Delivered Orders)', f"{i['fulfilled_items']:,}")
    c.metric('Freight-to-Sales Ratio', f"{f['freight_to_sales']:.1%}")
    st.divider()
    st.markdown('### 🚚 Freight Charged vs Product Price per Region')
    df = operations.regional_freight(con, filters)
    st.plotly_chart(px.bar(df, x='customer_state', y=['avg_product_price','avg_freight'],
                           barmode='group', labels={'value':'BRL','customer_state':'State'}),
                    use_container_width=True)
