@echo off
setlocal enabledelayedexpansion

:: === Lấy thư mục gốc (thư mục chứa file BAT) ===
cd /d "%~dp0"

:: === Đường dẫn tới script Python (tương đối) ===
set PY_SCRIPT=.\scripts\load.py

:: === Hỏi người dùng ngày LOAD ===
set /p data_date=👉 Nhập ngày cần LOAD (YYYY-MM-DD, Enter để dùng hôm nay): 

:: === Nếu người dùng để trống thì lấy ngày hiện tại bằng PowerShell ===
if "%data_date%"=="" (
    for /f %%i in ('powershell -Command "Get-Date -Format yyyy-MM-dd"') do set data_date=%%i
)

echo.
echo 📅 Ngày được chọn: %data_date%
echo 🚀 Đang chạy tiến trình LOAD...
echo ------------------------------------

:: === Gọi Python với tham số ngày ===
python "%PY_SCRIPT%" %data_date%

echo ------------------------------------
echo ✅ Hoàn tất! Nhấn phím bất kỳ để thoát.
pause >nul
