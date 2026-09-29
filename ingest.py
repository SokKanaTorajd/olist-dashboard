import duckdb
import os

# Path lokasi folder dataset kamu di Downloads (menggunakan raw string r"...")
DATA_DIR = r"C:\Users\user\Downloads\Olist_ecommerce_dataset"

# Lokasi file database DuckDB yang akan dibuat di folder projek
DB_PATH = "olist.duckdb"

# Pemetaan nama tabel DuckDB -> nama file CSV (lengkap sesuai foto)
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
        # Mengubah backslash Windows (\) jadi forward slash (/) agar aman di query DuckDB
        safe_path = csv_path.replace("\\", "/")
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM '{safe_path}'")
        print(f"✅ Tabel '{table_name}' berhasil dibuat!")
    else:
        print(f"⚠️ File tidak ditemukan: {csv_filename}")

con.close()
print("\n🎉 Selesai! Seluruh data sudah masuk ke file 'olist.duckdb'.")