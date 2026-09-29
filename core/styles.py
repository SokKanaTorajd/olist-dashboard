"""Shared CSS styling for the Olist dashboard."""

import streamlit as st


def apply_styles():
    """Apply the existing dashboard styling."""
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(35, 90, 112, .12), rgba(35, 90, 112, .04));
            border: 1px solid rgba(120, 160, 175, .22);
            padding: 1rem 1.1rem;
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
