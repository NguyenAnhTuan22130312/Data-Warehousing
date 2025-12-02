import os
import datetime
from configparser import ConfigParser
import sys, os
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.db_utils import connect_db, insert_log, update_log_status, get_log_by_id
from utils.email_utils import send_email



parser = argparse.ArgumentParser(description="ETL Player Data - Manual or Scheduled")
parser.add_argument('--manual', action='store_true', help='Chạy thủ công')
parser.add_argument('--date', type=str, help='Ngày chạy ETL (YYYY-MM-DD), mặc định hôm nay')
args = parser.parse_args()

job_name = "ETL_Player_Data"
start_time = datetime.datetime.now()
log_id = None
conn = None
cursor = None


# Xác định ngày chạy ETL
run_date = args.date or datetime.datetime.now().strftime("%Y-%m-%d")
print(f"Ngày chạy ETL: {run_date}")

try:
    # 2. Gọi kết nối DB ControlManagementDB  ở file D:\Data-Warehousing\scripts\etl_main.py  
    conn, cursor = connect_db()

    #4. Ghi lại log vào bảng log_history của DB ControlManagementDB  với trạng thái 
    #  RUNNING để bắt đầu quá trình ETL trong file D:\Data-Warehousing\utils\db_utils.py
    log_id = insert_log(cursor, job_name, start_time, "RUNNING")
    conn.commit()
    print(f"✅ Scheduler started at {start_time}")

    #Kiểm tra  bảng log_history của DB ControlManagementDB   có trạng thái RUNNNG của ETL  hay không ? 
    check_log = get_log_by_id(cursor, log_id)
    #chưa
    if not check_log or check_log["status"] != "RUNNING":
        raise Exception("❌ Không tìm thấy log RUNNING trong DB. Hủy tiến trình extract.")
    
    #Rồi
    # 5.Bắt đầu chạy file script D:\Data-Warehousing\script\extract.py
    print("Đang chạy extract.py ...")
    extract_cmd = f"python scripts/extract.py --date {run_date}"
    result_code = os.system(extract_cmd)

    if result_code != 0:
        raise Exception(f"extract.py thất bại với mã lỗi: {result_code}")
    

    # 6.8 Cập nhật lại log  quá trình ETL với trạng thái SUCCESS vào trong bảng Log_History của DB ControlManagementDB 
    end_time = datetime.datetime.now()
    update_log_status(cursor, log_id, "SUCCESS", end_time, records_processed=0)
    conn.commit()
    print("✅ Job completed successfully!")

    # 6.9 Đọc file cấu hình D:\Data-Warehousing\config\config.ini để lấy các tham số về email
    config = ConfigParser()
    config.read(os.path.join("config", "config.ini"))
    email_config = config["email"]
    receivers = [x.strip() for x in email_config["receiver"].split(",")]

    # 6.10 Gửi mail thông báo quá trình ETL đã thành công
    send_email(
        subject="[ETL SUCCESS] ETL_Player_Data Completed",
        body=f"Job ETL_Player_Data đã chạy thành công ✅\nThời gian: {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        to_list=receivers,
    )

except Exception as e:
    # Cập nhật trạng thái quá trình ETL thành FAILED vào trong bảng Log_History của DB ControlManagementDB
    end_time = datetime.datetime.now()
    if conn and log_id:
        update_log_status(cursor, log_id, "FAILED", end_time, error_message=str(e))
        conn.commit()
    # Gửi mail thông báo quá trình ETL đã thất bại 
    send_email(
        subject="[ETL FAILD] ETL_Player_Data FAILD",
        body=f"Job ETL_Player_Data đã chạy không  thành công ❌\nThời gian: {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        to_list=receivers,
    )
