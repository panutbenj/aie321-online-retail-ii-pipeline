import pandas as pd
from sqlalchemy import create_engine, text

# 1. เชื่อมต่อ PostgreSQL
DB_USER = "admin"
DB_PASS = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "kaggle_db"

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# 2. อ่านข้อมูลจากตารางใน Schema 'raw_data' เข้ามาเป็น DataFrame
query = "SELECT * FROM raw_data.online_retail_ii;"
df = pd.read_sql(query, engine)

# --- คำนวณรายการยกเลิกคำสั่งซื้อ (คำถามข้อ 6) จากข้อมูลดิบก่อนกรอง ---
df_raw_inv = df[df['Invoice'].astype(str).str.startswith("C", na=False)].copy()
cancelled_orders_summary = pd.DataFrame({
    "cancelled_rows": [len(df_raw_inv)],
    "cancelled_unique_invoices": [df_raw_inv['Invoice'].nunique()],
    "cancelled_total_quantity": [df_raw_inv["Quantity"].sum()]
})

# 3. การแปลง/ทำความสะอาดข้อมูลเบื้องต้น 
# --- 3.1 Feature Engineering ---
df_clean = df.copy()
df_clean = df_clean[(df_clean['Quantity'] > 0) & (df_clean['Price'] > 0)]
df_clean = df_clean.dropna(subset=['Customer ID'])
df_clean = df_clean.drop_duplicates()

df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'], format="%d/%m/%Y %H:%M", errors="coerce")
df_clean = df_clean.dropna(subset=["InvoiceDate"])

df_clean['Revenue'] = df_clean['Quantity'] * df_clean['Price']
df_clean['YearMonth'] = df_clean['InvoiceDate'].dt.to_period('M').astype(str)
df_clean["Month"] = df_clean["InvoiceDate"].dt.month

# --- 3.2 Aggregation ---
# ข้อ 2 & ข้อ 4: ยอดขายรวมรายเดือน / ช่วงเวลาที่มียอดขายสูงที่สุด
monthly_sales = (
    df_clean.groupby(["YearMonth", "Month"], as_index=False)
    .agg(
        total_revenue=("Revenue", "sum"),
        total_quantity=("Quantity", "sum"),
        total_orders=('Invoice', "nunique")
    )
    .sort_values("YearMonth")
)

# สรุปตามเลขเดือน (1-12) เพื่อดูช่วงเวลา/เดือนของปีที่มียอดขายสูงที่สุด
seasonality_by_month = (
    df_clean.groupby("Month", as_index=False)
    .agg(
        total_revenue=("Revenue", "sum"),
        total_quantity=("Quantity", "sum"),
        total_orders=('Invoice', "nunique")
    )
    .sort_values("total_revenue", ascending=False)
)

# ข้อ 1 & ข้อ 7: สินค้าขายดีที่สุด (ตามจำนวน) และสินค้าที่สร้างยอดขายรวมสูงสุด
product_performance = (
    df_clean.groupby(["StockCode", "Description"], as_index=False)
    .agg(
        total_quantity=("Quantity", "sum"),
        total_revenue=("Revenue", "sum"),
        total_orders=('Invoice', "nunique")
    )
    .sort_values("total_revenue", ascending=False)
)

# 4. บันทึกข้อมูลที่แปลงแล้วลง Schema ใหม่ (เช่น 'staging' หรือ 'clean_data') เพื่อแยกจากข้อมูลดิบใน raw_data
with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS production;"))
    conn.commit()

tables_to_save = {
    "online_retail_ii_clean": df_clean,
    "monthly_sales": monthly_sales,
    "seasonality_by_month": seasonality_by_month,
    "product_performance": product_performance,
    "cancelled_orders_summary": cancelled_orders_summary,
}

for t_name, t_df in tables_to_save.items():
    t_df.to_sql(
        name=t_name,
        con=engine,
        schema="production",
        if_exists="replace",
        index=False,
        chunksize=5000
    )
    print(f"บันทึก production.{t_name} สำเร็จ ({len(t_df)} แถว)")
