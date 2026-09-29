"""Load downloaded Olist CSV files into source tables in a local DuckDB database.

Update DATA_DIR before running. Existing matching source tables are replaced;
missing files are reported and skipped, so inspect the console output.
"""
import duckdb
import os

# Local directory containing the downloaded Olist CSV files; update for your machine.
DATA_DIR = r"C:\Users\user\Downloads\Olist_ecommerce_dataset"

# Output database in the project root.
DB_PATH = "olist.duckdb"

# Map source table names to the original Kaggle CSV filenames.
tables = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "product_category_translation": "product_category_name_translation.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv"
}

print("🚀 Memulai proses ingest dataset Olist ke DuckDB...")
con = duckdb.connect(DB_PATH)

for table_name, csv_filename in tables.items():
    csv_path = os.path.join(DATA_DIR, csv_filename)
    
    if os.path.exists(csv_path):
        # Normalize Windows path separators before using the CSV path in DuckDB SQL.
        safe_path = csv_path.replace("\\", "/")
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM '{safe_path}'")
        print(f"✅ Tabel '{table_name}' berhasil dibuat!")
    else:
        print(f"⚠️ File tidak ditemukan: {csv_filename}")

con.close()
print("\n🎉 Selesai! Seluruh data sudah masuk ke file 'olist.duckdb'.")