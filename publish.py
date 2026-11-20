import gspread
import pandas as pd
from sqlalchemy import create_engine

# 1. ตั้งค่าการเชื่อมต่อ PostgreSQL
DB_USER = "admin"
DB_PASS = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "kaggle_db"

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# 2. ตั้งค่า Google Sheets
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_NAME = "Online_Retail_II_Dashboard_Data"
MAX_ROWS_PER_SHEET = 50000  # ป้องกันลิมิต Cell ของ Google Sheets สำหรับตารางขนาดใหญ่

gc = gspread.service_account(filename=CREDENTIALS_FILE)

try:
    spreadsheet = gc.open(SPREADSHEET_NAME)
except gspread.SpreadsheetNotFound:
    spreadsheet = gc.create(SPREADSHEET_NAME)


def write_df_to_worksheet(df: pd.DataFrame, worksheet_name: str, max_rows: int | None = None):
    df_to_send = df.copy()

    for col in df_to_send.columns:
        if pd.api.types.is_datetime64_any_dtype(df_to_send[col]) or str(df_to_send[col].dtype).startswith("period"):
            df_to_send[col] = df_to_send[col].astype(str)

    df_to_send = df_to_send.replace([float("inf"), float("-inf")], None).fillna("")

    if max_rows is not None and len(df_to_send) > max_rows:
        df_to_send = df_to_send.head(max_rows)
        print(f"หมายเหตุ: จำกัดข้อมูล '{worksheet_name}' เหลือ {max_rows} แถวแรกตามข้อจำกัดของ Google Sheets")

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        worksheet.clear()
    except gspread.WorksheetNotFound:
        needed_rows = max(len(df_to_send) + 10, 100)
        needed_cols = max(len(df_to_send.columns) + 5, 20)
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=needed_rows, cols=needed_cols)

    values = [df_to_send.columns.tolist()] + df_to_send.values.tolist()
    worksheet.update(values=values, value_input_option="USER_ENTERED")
    print(f"ส่งข้อมูลขึ้น Worksheet '{worksheet_name}' สำเร็จ ({len(df_to_send)} แถว)")


def main():
    # 3. อ่านตารางสรุปและตารางหลักจาก Schema 'production'
    queries = {
        "monthly_sales": ("SELECT * FROM production.monthly_sales;", None),
        "seasonality_by_month": ("SELECT * FROM production.seasonality_by_month;", None),
        "top_products": ("SELECT * FROM production.product_performance LIMIT 500;", None),
        "cancelled_orders": ("SELECT * FROM production.cancelled_orders_summary;", None),
        "clean_transactions": ("SELECT * FROM production.online_retail_ii_clean;", MAX_ROWS_PER_SHEET),
    }

    for ws_name, (sql, row_limit) in queries.items():
        df_table = pd.read_sql(sql, engine)
        write_df_to_worksheet(df_table, ws_name, max_rows=row_limit)

    print("อัปโหลดข้อมูลจาก Schema production ขึ้น Google Sheets เรียบร้อย!")


if __name__ == "__main__":
    main()