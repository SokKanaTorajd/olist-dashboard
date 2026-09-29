from pathlib import Path

import duckdb
import streamlit as st


DB_PATH = Path(__file__).resolve().parent.parent / "olist.duckdb"


@st.cache_resource
def get_db_connection():
    """Return a cached, read-only connection to the Olist database."""
    if not DB_PATH.is_file():
        st.error("Database 'olist.duckdb' tidak ditemukan. Jalankan `python ingest.py` terlebih dahulu.")
        st.stop()

    return duckdb.connect(str(DB_PATH), read_only=True)
