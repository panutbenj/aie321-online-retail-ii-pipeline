import pandas as pd
from sqlalchemy import create_engine, text

# 1. ตั้งค่าการเชื่อมต่อ PostgreSQL
DB_USER = "admin"
DB_PASS = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "kaggle_db"

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# 2. อ่านไฟล์ online_retail_II.csv ที่อยู่ในโฟลเดอร์เดียวกัน
file_path = "online_retail_II.csv"
df = pd.read_csv(file_path, encoding="latin1")  # ใส่ encoding เผื่อไฟล์มีอักขระพิเศษ

# 3. ตรวจสอบ/สร้าง Schema 'raw_data'
with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw_data;"))
    conn.commit()

# 4. โหลดข้อมูลเข้าตารางใน Schema 'raw_data'
table_name = "online_retail_ii"

df.to_sql(
    name=table_name,
    con=engine,
    schema="raw_data",
    if_exists="replace",
    index=False,
    chunksize=5000  # แบ่งส่งทีละ 5,000 แถว ช่วยให้โหลดไฟล์ใหญ่ได้ลื่นขึ้น
)

print(f"นำเข้าข้อมูลลงตาราง raw_data.{table_name} สำเร็จ! (จำนวน {len(df)} แถว)")