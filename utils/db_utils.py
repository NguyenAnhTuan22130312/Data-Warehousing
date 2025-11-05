import mysql.connector
import datetime
import os
import configparser

def get_project_root():
    """Trả về D:\DATA-WAREHOUSING"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def connect_db():
    #3. Đọc file cấu hình D:\Data-Warehousing\config\config.ini để lấy cấu hình kết nối CSDL 
    root = get_project_root()
    
    # Đường dẫn tuyệt đối tới file config.ini
    config_path = os.path.join(root, "config", "config.ini")

    # Đọc file config.ini
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    db_cfg = config["databaseControlManagementDB"]

    # Kết nối MySQL
    conn = mysql.connector.connect(
        host=db_cfg["host"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        database=db_cfg["database"],
        port=int(db_cfg.get("port", 3306))
    )
    return conn, conn.cursor(dictionary=True)

def insert_log(cursor, job_name, start_time,  status):
    cursor.execute("""
        INSERT INTO log_history (job_name, start_time, status)
        VALUES (%s, %s, %s)
    """, (job_name, start_time, status))
    return cursor.lastrowid

def insert_log_new(cursor, job_name, end_time, error_message, created_at, status):
    cursor.execute("""
        INSERT INTO log_history (job_name, end_time, error_message, created_at,  status)
        VALUES (%s, %s, %s, %s, %s)
    """, (job_name, end_time, error_message, created_at, status))
    return cursor.lastrowid


def update_log_status(cursor, log_id, status, end_time, records_processed=0, error_message=None):
    cursor.execute("""
        UPDATE log_history
        SET end_time=%s, status=%s, records_processed=%s, error_message=%s
        WHERE id=%s
    """, (end_time, status, records_processed, error_message, log_id))


def insert_log_history(cursor, job_name, source_id, status, records_processed=0, error_message=None):
    """
    Ghi log kết quả chạy ETL (SUCCESS / FAILED) vào bảng log_history
    """
    try:
        start_dt = datetime.datetime.now() - datetime.timedelta(seconds=120)  # ước lượng thời điểm bắt đầu
        end_dt = datetime.datetime.now()

        cursor.execute("""
            INSERT INTO log_history 
            (job_name, source_id, start_time, end_time, status, records_processed, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            job_name,
            source_id,
            start_dt,
            end_dt,
            status,
            records_processed,
            error_message
        ))
        print(f"✅ Ghi log thành công cho job {job_name} ({status})")

    except Exception as e:
        print(f"❌ Lỗi khi ghi log_history: {e}")