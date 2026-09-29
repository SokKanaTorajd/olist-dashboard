import streamlit as st
import plotly.express as px
from core.metrics import financial


def render(con, filters):
    st.subheader('Executive KPI Summary')
    k = financial.overview(con, filters)
    a, b, c, d = st.columns(4)
    a.metric('Total Revenue (GMV)', f"R$ {k['total_sales']:,.2f}")
    b.metric('Total Orders', f"{k['total_orders']:,}")
    c.metric('Average Order Value (AOV)', f"R$ {k['aov']:,.2f}")
    d.metric('Unique Customers', f"{k['unique_customers']:,}")
    a, b, c = st.columns(3)
    a.metric('Total Items Sold (Order Items)', f"{k['total_items']:,}")
    b.metric('Items per Order', f"{k['basket_size']:.2f}")
    c.metric('Sales per Unique Customer', f"R$ {k['sales_per_customer']:,.2f}",
             help='Total product sales / distinct customer_unique_id; not lifetime value.')
    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown('### 📈 Monthly Revenue Trend (GMV)')
        df = financial.monthly_sales(con, filters)
        st.plotly_chart(px.line(df, x='month', y='gmv', markers=True,
                                labels={'gmv':'Revenue (BRL)', 'month':'Month'}),
                        use_container_width=True)
    with right:
        st.markdown('### 🏆 Top 10 Product Categories by GMV')
        df = financial.top_categories(con, filters)
        fig = px.bar(df, x='total_gmv', y='category', orientation='h',
                     color='total_gmv', color_continuous_scale='Blues')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
