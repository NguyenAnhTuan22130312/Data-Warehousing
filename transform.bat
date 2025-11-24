@echo off
cd /d "D:\Data-Warehousing"
set /p input_date="Nhập ngày (YYYY-MM-DD): "
python scripts\transform.py %input_date%
pause
