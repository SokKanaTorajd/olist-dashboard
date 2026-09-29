import os
import re
from io import BytesIO

import duckdb
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner="Reading CSV file…")
def explorer_load_csv(file_bytes: bytes, separator: str | None) -> pd.DataFrame:
    """Read an uploaded CSV while keeping the Streamlit cache key stable."""
    return pd.read_csv(
        BytesIO(file_bytes),
        sep=separator,
        engine="python" if separator is None else "c",
    )


@st.cache_data(show_spinner="Loading table from DuckDB…")
def explorer_load_duckdb_table(db_path: str, table_name: str) -> pd.DataFrame:
    """Fetch a full table from local DuckDB into a DataFrame."""
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute(f'SELECT * FROM "{table_name.replace(chr(34), chr(34) * 2)}"').df()
    con.close()
    return df


def explorer_date_columns(frame: pd.DataFrame) -> dict[str, pd.Series]:
    """Return columns that look like dates, without changing the source data."""
    parsed: dict[str, pd.Series] = {}
    for column in frame.columns:
        values = frame[column]
        if pd.api.types.is_datetime64_any_dtype(values):
            parsed[column] = pd.to_datetime(values, errors="coerce")
        elif re.search(r"date|time|timestamp", str(column), flags=re.IGNORECASE):
            candidate = pd.to_datetime(values, errors="coerce")
            if candidate.notna().sum() >= max(2, int(len(frame) * 0.5)):
                parsed[column] = candidate
    return parsed


def explorer_format_bytes(size: int) -> str:
    units = ("B", "KB", "MB", "GB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"



def render():
    st.subheader("🔎 General Data Explorer")
    st.caption("Explore Olist datasets via local DuckDB or manual CSV uploads.")

    # --- SIDEBAR DATA SOURCE ---
    with st.sidebar:
        st.header("Your data")
        data_source = st.radio(
            "Data Source",
            ["DuckDB (olist.duckdb)", "Upload CSV File"],
            index=0 if os.path.exists("olist.duckdb") else 1
        )

        data = None
        file_name = "DuckDB Table"
        file_size = 0

        if data_source == "DuckDB (olist.duckdb)":
            if not os.path.exists("olist.duckdb"):
                st.error("File 'olist.duckdb' tidak ditemukan. Jalankan `python ingest.py` terlebih dahulu.")
                return
        
            con = duckdb.connect("olist.duckdb", read_only=True)
            tables_list = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
            con.close()

            selected_table = st.selectbox("Select Table", tables_list)
            if selected_table:
                data = explorer_load_duckdb_table("olist.duckdb", selected_table)
                file_name = f"olist.duckdb -> {selected_table}"
                file_size = os.path.getsize("olist.duckdb")

        else:
            uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
            separator_label = st.selectbox(
                "Delimiter",
                ("Auto-detect", "Comma (,)", "Semicolon (;)", "Tab", "Pipe (|)"),
            )
            separator = {
                "Auto-detect": None,
                "Comma (,)": ",",
                "Semicolon (;)": ";",
                "Tab": "\t",
                "Pipe (|)": "|",
            }.get(separator_label)

            if uploaded_file is not None:
                try:
                    data = explorer_load_csv(uploaded_file.getvalue(), separator)
                    file_name = uploaded_file.name
                    file_size = uploaded_file.size
                except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
                    st.error(f"Could not read this CSV: {error}")
                    st.info("Check the file encoding and delimiter, then try again.")
                    return

    if data is None:
        st.info("Pilih tabel DuckDB atau unggah file CSV di sidebar untuk mulai mengeksplorasi.")
        return

    if data.empty and len(data.columns) == 0:
        st.error("This dataset does not contain any readable columns.")
        return

    st.success(f"Loaded **{len(data):,} rows** and **{len(data.columns):,} columns**.")

    missing_cells = int(data.isna().sum().sum())
    duplicate_rows = int(data.duplicated().sum())
    metric_columns = st.columns(4)
    metric_columns[0].metric("Rows", f"{len(data):,}")
    metric_columns[1].metric("Columns", f"{len(data.columns):,}")
    metric_columns[2].metric("Missing cells", f"{missing_cells:,}")
    metric_columns[3].metric("Duplicate rows", f"{duplicate_rows:,}")

    # --- FILTERS ---
    with st.sidebar:
        st.divider()
        st.header("Filters")
        filtered = data.copy()
        date_fields = explorer_date_columns(data)

        with st.expander("Filter categories", expanded=False):
            category_columns = [
                column
                for column in data.columns
                if (pd.api.types.is_object_dtype(data[column])
                    or pd.api.types.is_string_dtype(data[column])
                    or pd.api.types.is_bool_dtype(data[column]))
                and data[column].nunique(dropna=True) <= 100
            ]
            for column in category_columns:
                options = sorted(data[column].dropna().astype(str).unique().tolist())
                selected = st.multiselect(
                    str(column), options, key=f"category-{column}"
                )
                if selected:
                    filtered = filtered[filtered[column].astype(str).isin(selected)]

        with st.expander("Filter dates", expanded=False):
            for column, parsed_dates in date_fields.items():
                valid_dates = parsed_dates.dropna()
                if valid_dates.empty:
                    continue
                date_range = st.date_input(
                    str(column),
                    value=(valid_dates.min().date(), valid_dates.max().date()),
                    key=f"date-{column}",
                )
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    row_dates = parsed_dates
                    filtered = filtered[
                        row_dates.loc[filtered.index].dt.date.between(start_date, end_date)
                    ]

        with st.expander("Filter numeric ranges", expanded=False):
            numeric_columns = data.select_dtypes(include="number").columns.tolist()
            for column in numeric_columns:
                minimum = data[column].min()
                maximum = data[column].max()
                if pd.isna(minimum) or pd.isna(maximum) or minimum == maximum:
                    continue
                limits = st.slider(
                    str(column),
                    min_value=float(minimum),
                    max_value=float(maximum),
                    value=(float(minimum), float(maximum)),
                    key=f"range-{column}",
                )
                filtered = filtered[filtered[column].between(*limits) | filtered[column].isna()]

    st.caption(f"Showing {len(filtered):,} of {len(data):,} rows after filters.")
    overview_tab, chart_tab, quality_tab, data_tab = st.tabs(
        ("Overview", "Explore", "Data quality", "Data")
    )

    with overview_tab:
        left, right = st.columns((1.25, 1))
        with left:
            st.subheader("Column types")
            type_summary = data.dtypes.astype(str).value_counts().rename_axis("Data type").reset_index(name="Columns")
            st.dataframe(type_summary, hide_index=True, use_container_width=True)
        with right:
            st.subheader("Quick profile")
            st.write(f"**Source / File:** {file_name}")
            st.write(f"**Size:** {explorer_format_bytes(file_size)}")
            st.write(f"**Numeric columns:** {len(data.select_dtypes(include='number').columns)}")
            st.write(f"**Date-like columns:** {len(date_fields)}")

        st.subheader("Numeric summary")
        numeric_data = filtered.select_dtypes(include="number")
        if numeric_data.empty:
            st.info("No numeric columns are available in the filtered data.")
        else:
            st.dataframe(numeric_data.describe().T, use_container_width=True)

    with chart_tab:
        st.subheader("Build a quick chart")
        if filtered.empty:
            st.warning("No rows match the selected filters.")
        else:
            all_columns = filtered.columns.tolist()
            chart_columns = st.columns(3)
            x_column = chart_columns[0].selectbox("X-axis", all_columns)
            numeric_options = filtered.select_dtypes(include="number").columns.tolist()
            y_options = ["Row count"] + numeric_options
            y_column = chart_columns[1].selectbox("Measure", y_options)
            chart_type = chart_columns[2].selectbox("Chart", ("Bar", "Line", "Scatter"))

            if y_column == "Row count":
                plot_data = filtered[x_column].astype(str).value_counts().head(50).sort_values(ascending=False)
                st.bar_chart(plot_data, use_container_width=True)
            elif chart_type == "Scatter":
                st.scatter_chart(filtered, x=x_column, y=y_column, use_container_width=True)
            else:
                plot_data = filtered.groupby(x_column, dropna=False)[y_column].sum(min_count=1)
                plot_data = plot_data.sort_values(ascending=False).head(50) if chart_type == "Bar" else plot_data.sort_index()
                if chart_type == "Bar":
                    st.bar_chart(plot_data, use_container_width=True)
                else:
                    st.line_chart(plot_data, use_container_width=True)
            st.caption("Charts display up to 50 categories for readability.")

    with quality_tab:
        st.subheader("Missing values by column")
        missing_summary = pd.DataFrame(
            {
                "Missing": data.isna().sum(),
                "Missing %": (data.isna().mean() * 100).round(2),
                "Unique values": data.nunique(dropna=True),
                "Data type": data.dtypes.astype(str),
            }
        ).sort_values("Missing", ascending=False)
        st.dataframe(missing_summary, use_container_width=True)
        if duplicate_rows:
            st.warning(f"There are {duplicate_rows:,} fully duplicated rows in the uploaded file.")
        else:
            st.success("No fully duplicated rows found.")

    with data_tab:
        st.subheader("Filtered data preview")
        preview_rows = st.slider(
            "Rows to preview", min_value=10, max_value=500, value=100, step=10
        )
        st.dataframe(filtered.head(preview_rows), use_container_width=True, height=520)
        st.download_button(
            "Download filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name=f"{file_name.split(' ')[0]}_filtered.csv",
            mime="text/csv",
        )
