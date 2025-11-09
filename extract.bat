@echo off
cd /d "D:\Data-Warehousing"
set /p input_date="Nhập ngày (YYYY-MM-DD): "
python scripts\etl_main.py --date %input_date%
pause