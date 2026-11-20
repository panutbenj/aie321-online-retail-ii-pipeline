# Online Retail II — Automated End-to-End Data Pipeline

โปรเจกต์สร้างไปป์ไลน์ข้อมูลอัตโนมัติ (Automated Data Pipeline) แบบครบวงจร โดยใช้ชุดข้อมูล **Online Retail II** จาก Kaggle เพื่อนำเข้าข้อมูลดิบ ทำความสะอาด แปลงข้อมูล สรุปผลตามคำถามทางธุรกิจ และส่งออกขึ้นคลาวด์เพื่อนำไปสร้าง Interactive Dashboard บน Google Looker Studio (Data Studio)

---

## 1. สถาปัตยกรรมข้อมูลและเครื่องมือที่ใช้ (Architecture & Tech Stack)

```text
[Kaggle CSV] ──► (ingest.py) ──► [PostgreSQL: raw_data]
                                        │
                                 (transform.py)
                                        ▼
[Looker Studio] ◄── [Google Sheets] ◄── (publish.py) ◄── [PostgreSQL: production]
```


* **Data Source:** ชุดข้อมูล [Online Retail II](https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset) (`online_retail_II.csv`)(เฉพาะปี 2010-2011)
* **Data Warehouse:** PostgreSQL 16 (รันบน Docker Container) แบ่งออกเป็น 2 Schemas:
  * `raw_data`: เก็บข้อมูลดิบที่นำเข้าจากไฟล์ CSV
  * `production`: เก็บข้อมูลที่ผ่านการทำความสะอาด (Cleaned Data) และตารางสรุปผล (Aggregated Tables)
* **ETL & Automation:** Python (`pandas`, `sqlalchemy`, `psycopg2-binary`, `gspread`)
* **Cloud Staging & BI Visualization:** Google Sheets & Google Looker Studio (Data Studio)

---

## 2. คำถามทางธุรกิจที่ต้องการวิเคราะห์ (Business Questions)

1. **สินค้าขายดีที่สุดตามจำนวน:** สินค้าใดมียอดขาย (จำนวนชิ้น) สูงที่สุด?
2. **ยอดขายรวมรายเดือน:** แนวโน้มยอดขายรวมในแต่ละเดือนเป็นอย่างไร?
3. **ช่วงเวลาที่มียอดขายสูงที่สุด:** เดือนใดของปีที่สร้างยอดขายได้สูงสุด (Seasonality)?
4. **รายการยกเลิกคำสั่งซื้อ:** มีจำนวนรายการและจำนวนใบแจ้งหนี้ที่ถูกยกเลิก (เลขที่ใบแจ้งหนี้ขึ้นต้นด้วย `C`) เท่าไร?
5. **สินค้าที่สร้างยอดขายรวมสูงสุด:** สินค้าใดทำรายได้รวม (Revenue) ให้กับร้านค้าสูงที่สุด?

---

## 3. โครงสร้างไฟล์ในโปรเจกต์ (Project Structure)

```text
├── docker-compose.yml   # ไฟล์ตั้งค่า PostgreSQL Container บน Docker
├── ingest.py            # สคริปต์อ่านไฟล์ CSV และโหลดลง Schema 'raw_data'
├── transform.py         # สคริปต์ทำความสะอาดข้อมูล สร้าง Feature และสรุปผลลง Schema 'production'
├── publish.py           # สคริปต์ดึงข้อมูลจาก 'production' ส่งขึ้น Google Sheets
├── run_pipeline.py      # สคริปต์หลักสำหรับสั่งรัน Pipeline ทั้งหมดต่อเนื่องในคำสั่งเดียว
├── .gitignore           # กำหนดไฟล์ที่ยกเว้นไม่ให้อัปโหลดขึ้น Git (เช่น credentials.json, *.csv)
└── README.md            # เอกสารอธิบายโปรเจกต์และวิธีรันระบบ
```

---

## 4. วิธีการติดตั้งและรันโปรเจกต์ (Setup & Execution)

### ขั้นตอนที่ 1: เตรียมสภาพแวดล้อมและ Dependencies
1. โคลน Repository นี้ลงบนเครื่อง:
```bash
   git clone <YOUR_GITHUB_REPOSITORY_URL>
   cd <YOUR_PROJECT_FOLDER>
```
2. ติดตั้ง Python Libraries ที่จำเป็น:
```bash
   pip install gspread pandas sqlalchemy psycopg2-binary
```

### ขั้นตอนที่ 2: เตรียมข้อมูลและ Google API Credentials
1. ดาวน์โหลดชุดข้อมูล **Online Retail II** จาก Kaggle และวางไฟล์ `online_retail_II.csv` ไว้ในโฟลเดอร์หลักของโปรเจกต์
2. สร้าง Service Account บน **Google Cloud Console** พร้อมเปิดใช้งาน **Google Sheets API** และ **Google Drive API**
3. ดาวน์โหลดไฟล์คีย์ JSON มาวางไว้ในโฟลเดอร์หลักและตั้งชื่อเป็น **`credentials.json`** *(ห้าม commit ไฟล์นี้ขึ้น GitHub)*
4. สร้างไฟล์ Google Sheet ชื่อ `Online_Retail_II_Dashboard_Data` บน Google Drive และแชร์สิทธิ์ **Editor** ให้กับ `client_email` ที่อยู่ในไฟล์ `credentials.json`

### ขั้นตอนที่ 3: เปิดฐานข้อมูล PostgreSQL ด้วย Docker
รันคำสั่งต่อไปนี้เพื่อสร้างและเปิดใช้งาน PostgreSQL Container:
```bash
docker compose up -d
```
*(ค่าเชื่อมต่อฐานข้อมูล: Host `localhost`, Port `5432`, Database `kaggle_db`, User `admin`, Password `admin`)*

### ขั้นตอนที่ 4: รัน Data Pipeline แบบครบวงจร
สั่งทำงานทุกขั้นตอน (`ingest.py` -> `transform.py` -> `publish.py`) ต่อเนื่องกันด้วยคำสั่งเดียว:
```bash
python run_pipeline.py
```

---

## 5. Dashboard & Deliverables

* **Looker Studio (Data Studio) Dashboard:** `https://datastudio.google.com/reporting/bcf53d93-5f1f-4fb4-be5f-72c106503497`