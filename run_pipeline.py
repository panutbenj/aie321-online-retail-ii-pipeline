import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

STEPS = [
    ("Ingestion (raw_data)", BASE_DIR / "ingest.py"),
    ("Transformation (production)", BASE_DIR / "transform.py"),
    ("Publish (Google Sheets)", BASE_DIR / "publish.py"),
]


def run_step(step_name: str, script_path: Path):
    if not script_path.exists():
        raise FileNotFoundError(f"ไม่พบไฟล์สคริปต์: {script_path}")

    print(f"\n{'=' * 50}")
    print(f"เริ่มทำงาน: {step_name} ({script_path.name})")
    print(f"{'=' * 50}")

    start_time = time.time()
    result = subprocess.run([sys.executable, str(script_path)], check=False)
    elapsed = time.time() - start_time

    if result.returncode != 0:
        raise RuntimeError(f"ขั้นตอน '{step_name}' ล้มเหลว (exit code {result.returncode}) หลังผ่านไป {elapsed:.1f} วินาที")

    print(f"เสร็จสิ้น: {step_name} ใน {elapsed:.1f} วินาที")


def main():
    pipeline_start = time.time()
    print("เริ่มต้นรัน Data Pipeline แบบครบวงจร...")

    for step_name, script_path in STEPS:
        run_step(step_name, script_path)

    total_elapsed = time.time() - pipeline_start
    print(f"\nรัน Pipeline สำเร็จครบทุกขั้นตอนใน {total_elapsed:.1f} วินาที!")


if __name__ == "__main__":
    main()