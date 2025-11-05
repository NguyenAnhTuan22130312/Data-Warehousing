import os
import datetime
from configparser import ConfigParser
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.db_utils import connect_db, insert_log, update_log_status
from utils.email_utils import send_email


job_name = "ETL_Player_Data"
start_time = datetime.datetime.now()
log_id = None
conn = None
cursor = None

try:
    # 2. Gọi kết nối DB ControlManagementDB  trong file D:\Data-Warehousing\utils\db_utils.py
    conn, cursor = connect_db()
    # 4. Ghi lại log với trạng thái RUNNING để bắt đầu quá trình ETL
    log_id = insert_log(cursor, job_name, start_time, "RUNNING")
    conn.commit()
    print(f"✅ Scheduler started at {start_time}")

    # 5. Gọi script extract.py
    print("Đang chạy file extract.py ...")
    result_code = os.system("python scripts/extract.py")

    # 6.8 cập nhật lại log  quá trình ETL với trạng thái SUCCESS
    end_time = datetime.datetime.now()
    update_log_status(cursor, log_id, "SUCCESS", end_time, records_processed=0)
    conn.commit()
    print("✅ Job completed successfully!")

    # 6.9 Đọc file cấu hình để lấy các tham số về email
    config = ConfigParser()
    config.read(os.path.join("config", "config.ini"))
    email_config = config["email"]
    receivers = [x.strip() for x in email_config["receiver"].split(",")]

    # 6.10 Gửi mail thông báo  thành công
    send_email(
        subject="[ETL SUCCESS] ETL_Player_Data Completed",
        body=f"Job ETL_Player_Data đã chạy thành công ✅\nThời gian: {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        to_list=receivers,
    )
    # 7. Truy cập file transform.py để thực hiện Transform
    print("Đang chạy file transform.py ...")
    result_code = os.system("python scripts/transform.py")

except Exception as e:
    # Cập nhật trạng thái quá trình ETL thành FAILED
    end_time = datetime.datetime.now()
    if conn and log_id:
        update_log_status(cursor, log_id, "FAILED", end_time, error_message=str(e))
        conn.commit()
    # Gửi mail thông báo thất bại
    send_email(
        subject="[ETL FAILD] ETL_Player_Data FAILD",
        body=f"Job ETL_Player_Data đã chạy không  thành công ❌\nThời gian: {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        to_list=receivers,
    )
