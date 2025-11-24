#!/bin/bash

# Lấy thư mục script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit

# Kích hoạt venv
source venv/bin/activate

# Nhập ngày
read -p "Nhập ngày (YYYY-MM-DD): " input_date

# Chạy Python script với tham số --date
# 9. Tự động chạy D:\Data-Warehousing\scripts\build_datamart.py
python3 scripts/build_datamart.py --date "$input_date"

read -p "Nhấn Enter để thoát..."
