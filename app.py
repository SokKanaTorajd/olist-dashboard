import streamlit as st
from core.database import get_db_connection
from core.filters import render_global_filters
from core.styles import apply_styles
from tabs import customer, executive, explorer, finance, operations

st.set_page_config(page_title='Olist Data Explorer', page_icon='🛍️', layout='wide')
apply_styles()
con = get_db_connection()
st.title('🛍️ Olist E-Commerce Data Explorer')
st.caption('Multi-Perspective Enterprise Analytics powered by DuckDB & Streamlit')
filters = render_global_filters(con)

tab_exec, tab_fin, tab_ops, tab_cx, tab_explorer = st.tabs([
    '🏛️ Executive Overview', '💳 Finance & Marketing', '🚚 Operations & Logistics',
    '⭐ Customer Experience', '🔎 Data Explorer'])
with tab_exec:
    executive.render(con, filters)
with tab_fin:
    finance.render(con, filters)
with tab_ops:
    operations.render(con, filters)
with tab_cx:
    customer.render(con, filters)
with tab_explorer:
    explorer.render()
