import mysql.connector
import csv
import datetime
import configparser
import os
import sys
import re

# Lấy đường dẫn thư mục gốc của dự án (thư mục cha của 'scripts')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Thêm thư mục gốc vào sys.path để import các module (nếu cần, giống extract.py)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ----- SỬ DỤNG EMAIL_UTILS -----
try:
    from utils.email_utils import send_email
except ImportError:
    print("⚠️ Cảnh báo: Không thể import 'send_email' từ 'utils.email_utils'.")

    def send_email(subject, body, to_list):
        print("--- LỖI GIẢ LẬP (do không import được): ---")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print("------------------------------------------")


def check_extract_success(data_date_str: str, config):
    db_conn = None
    db_cursor = None
    try:
        # Đọc config của DB Control
        db_config = config["databaseControlManagementDB"]

        # 7.1. KẾT NỐI CONTROLMANAGEMENTDB
        db_conn = mysql.connector.connect(
            host=db_config.get("host"),
            user=db_config.get("user"),
            password=db_config.get("password"),
            database=db_config.get("database"),
            port=db_config.get("port"),
        )
        db_cursor = db_conn.cursor()
        print(f"✅ Đã kết nối ControlManagementDB để kiểm tra log.")

        required_logs = [
            "extract_player_stats_top5",
            "extract_player_stats_overview",
            "extract_player_stats_performance",
        ]

        # 7.2. TRUY VẤN LOG_HISTORY (theo ngày hôm nay)
        sql_check = """
            SELECT COUNT(DISTINCT job_name) 
            FROM log_history
            WHERE status = 'SUCCESS'
            AND job_name IN (%s, %s, %s)
            AND DATE(created_at) = %s 
        """

        db_cursor.execute(
            sql_check,
            (required_logs[0], required_logs[1], required_logs[2], data_date_str),
        )

        success_count = db_cursor.fetchone()[0]

        # ĐIỀU KIỆN: TÌM THẤY 3 LOGS "SUCCESS" CỦA EXTRACT?
        if success_count == 3:
            print(
                f"✅ Đã xác nhận 3/3 logs extract thành công cho ngày {data_date_str}."
            )
            return True, None
        else:
            # Luồng 'Không ❌'
            error_msg = f"Chưa tìm thấy đủ 3 logs extract thành công. (Tìm thấy: {success_count}/3)"
            print(f"⚠️ {error_msg}")
            return False, error_msg  # Dẫn đến 7.2.a (Gửi mail lỗi)

    except Exception as e:
        error_msg = f"Lỗi nghiêm trọng khi kiểm tra log: {e}"
        print(f"❌ {error_msg}")
        return False, error_msg  # Dẫn đến 7.2.a (Gửi mail lỗi)
    finally:
        if db_cursor:
            db_cursor.close()
        if db_conn:
            db_conn.close()
        print("Đã đóng kết nối CSDL ControlManagementDB.")


def transform_and_load(data_date_str: str, config):
    conn = None
    cursor = None
    record_count = 0  # Biến đếm số dòng load vào player_staging

    try:
        # Đọc cấu hình
        db_config = config["databasePerformance_Staging"]

        # Thiết lập các biến
        load_batch_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_filename = f"staging_player_stats_{data_date_str}.csv"
        input_file = os.path.join(PROJECT_ROOT, "data", target_filename)

        # 7.3. KIỂM TRA FILE .CSV TỒN TẠI?
        if not os.path.exists(input_file):
            # Nếu 'Không ❌', trả về lỗi (sẽ được xử lý ở 7.2.a)
            error_msg = (
                f"Không tìm thấy file CSV cho ngày '{data_date_str}': {input_file}"
            )
            print(f"❌ Lỗi: {error_msg}")
            return False, error_msg, 0  # Trả về 0 records

        # Nếu 'Có ✅', tiếp tục
        print(f"Bắt đầu xử lý file: {input_file}")
        print(f"Load Batch ID: {load_batch_id}")

        # 7.4. KẾT NỐI CSDL STAGING, DELETE, LOAD, COMMIT
        print(f"✅ Kết nối thành công đến cơ sở dữ liệu: {db_config.get('database')}")
        conn = mysql.connector.connect(
            host=db_config.get("host"),
            user=db_config.get("user"),
            password=db_config.get("password"),
            database=db_config.get("database"),
            port=db_config.get("port"),
        )
        cursor = conn.cursor()

        player_data_to_load = []
        date_data_to_load = {}

        # 7.5 Đọc file csv và transform
        with open(input_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                api_date_str = row.get("api_date")
                if not api_date_str or api_date_str != data_date_str:
                    continue

                date_obj = datetime.datetime.strptime(api_date_str, "%Y-%m-%d")
                date_key = date_obj.strftime("%Y%m%d")

                player_tuple = (
                    row.get("player_id"),
                    row.get("player_name"),
                    row.get("team_id"),
                    row.get("team_name"),
                    row.get("nationality"),
                    row.get("position"),
                    row.get("age"),
                    row.get("height"),
                    row.get("weight"),
                    row.get("dominant_foot"),
                    row.get("rating"),
                    row.get("metric_type"),
                    row.get("metric_value"),
                    row.get("duelWon"),
                    row.get("passSuccess"),
                    row.get("assist"),
                    row.get("shotOnTarget"),
                    row.get("api_date"),
                    row.get("extract_time"),
                    date_key,
                    load_batch_id,
                )
                player_data_to_load.append(player_tuple)

                if api_date_str not in date_data_to_load:
                    year, month, day = date_obj.year, date_obj.month, date_obj.day
                    quarter = (month - 1) // 3 + 1
                    day_of_week, day_name = date_obj.isoweekday(), date_obj.strftime(
                        "%A"
                    )
                    month_name, is_weekend = date_obj.strftime("%B"), (
                        "1" if day_of_week >= 6 else "0"
                    )
                    date_tuple = (
                        date_key,
                        api_date_str,
                        api_date_str,
                        str(year),
                        str(quarter),
                        str(month).zfill(2),
                        str(day).zfill(2),
                        str(day_of_week),
                        day_name,
                        month_name,
                        is_weekend,
                        load_batch_id,
                    )
                    date_data_to_load[api_date_str] = date_tuple

        # 7.5.1 Xóa data snap short cũ
        print(f"Đang dọn dẹp dữ liệu cũ cho api_date = '{data_date_str}'...")
        cursor.execute(
            "DELETE FROM player_staging WHERE api_date = %s", (data_date_str,)
        )
        print(f"Đã xóa {cursor.rowcount} bản ghi cũ.")

        # 7.5.2 Load data mới vào table date_staging và player_staging
        if date_data_to_load:
            date_values = list(date_data_to_load.values())
            sql_date = """INSERT IGNORE INTO date_staging (date_key, api_date, full_date, year, quarter, month, day, day_of_week, day_name, month_name, is_weekend, load_batch) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(sql_date, date_values)
            print(
                f"✅ Đã load {cursor.rowcount} bản ghi (ngày duy nhất) vào date_staging."
            )

        if player_data_to_load:
            sql_player = """INSERT INTO player_staging (player_id, player_name, team_id, team_name, nationality, position, age, height, weight, dominant_foot, rating, metric_type, metric_value, duelWon, passSuccess, assist, shotOnTarget, api_date, extract_time, date_key, load_batch) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(sql_player, player_data_to_load)
            record_count = cursor.rowcount
            print(f"✅ Đã load {record_count} bản ghi vào player_staging.")

        conn.commit()
        # 7.6 Kết thúc Thông báo transform thành công (SUCEESD)
        print("🎉 Transform và Load hoàn tất!")
        return True, None, record_count

    except Exception as e:
         # 7.7 Kết thúc Thông báo transform thành công (SUCEESD)
        error_msg = f"Lỗi trong quá trình Transform/Load: {e}"
        print(f"❌ {error_msg}")
        if conn:
            conn.rollback()
        return False, error_msg, 0
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("Đã đóng kết nối CSDL Performance_Staging.")


def is_valid_date(date_string):
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_string):
        try:
            datetime.datetime.strptime(date_string, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    return False


# LUỒNG ĐIỀU KHIỂN CHÍNH
if __name__ == "__main__":

    config = configparser.ConfigParser()
    config_path = os.path.join(PROJECT_ROOT, "config", "config.ini")

    if not os.path.exists(config_path):
        print(f"❌ Lỗi nghiêm trọng: Không tìm thấy file config.ini tại {config_path}")
        sys.exit(1)

    config.read(config_path)

    # --- Biến để ghi log ---
    start_time = datetime.datetime.now()
    date_to_process = None
    should_run_transform = False
    error_message = ""
    records_loaded = 0

    # Task Scheduler chạy file không có tham số, nên sẽ vào nhánh 'else'
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
        if is_valid_date(date_arg):
            print(f"🚀 Bắt đầu chạy transform CHỈ ĐỊNH cho ngày: {date_arg}")
            date_to_process = date_arg
            should_run_transform = True
            print("Chạy ở chế độ MANUAL, bỏ qua kiểm tra log.")
        else:
            error_message = (
                f"Lỗi: Định dạng ngày '{date_arg}' không hợp lệ. Phải là YYYY-MM-DD."
            )
            print(f"❌ {error_message}")

    else:
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        print(f"🚀 Bắt đầu chạy transform TỰ ĐỘNG cho ngày hôm nay: {today_date}")
        date_to_process = today_date

        # --- THỰC HIỆN BƯỚC 7.1, 7.2 VÀ ĐIỀU KIỆN ---
        print(f"Bắt đầu kiểm tra log extract cho ngày {date_to_process}...")
        success, log_error = check_extract_success(date_to_process, config)

        if success:
            should_run_transform = True  # Log OK -> Dẫn đến 7.2.a
        else:
            error_message = log_error  # Log không OK -> Dẫn đến 7.3

    # --- THỰC HIỆN BƯỚC 7.3, 7.4 ---
    if date_to_process and should_run_transform:
        # Chỉ chạy nếu (có ngày) VÀ (được phép chạy)
        success_transform, transform_error, records_loaded = transform_and_load(
            date_to_process, config
        )

        if not success_transform:
            error_message = transform_error  # Dẫn đến 7.2.a

    elif not error_message:
        if not date_to_process:
            error_message = "Lỗi định dạng ngày (Manual) hoặc không có ngày xử lý."

    # ----- 7.8 GHI LOG VÀO DATABASE log_history-----
    end_time = datetime.datetime.now()
    log_status = "FAILED" if error_message else "SUCCESS"

    log_conn = None
    log_cursor = None
    try:
        # Kết nối CSDL Control để GHI log
        log_db_config = config["databaseControlManagementDB"]
        log_conn = mysql.connector.connect(
            host=log_db_config.get("host"),
            user=log_db_config.get("user"),
            password=log_db_config.get("password"),
            database=log_db_config.get("database"),
            port=log_db_config.get("port"),
        )
        log_cursor = log_conn.cursor()

        # Insert log
        log_sql = """
            INSERT INTO log_history 
            (job_name, start_time, end_time, status, records_processed, error_message) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        log_values = (
            "transform_staging_load",  # Tên job của script này
            start_time,
            end_time,
            log_status,
            records_loaded,
            error_message if error_message else None,
        )
        log_cursor.execute(log_sql, log_values)
        log_conn.commit()
        print(f"✅ Đã ghi log '{log_status}' cho 'transform_staging_load'.")

    except Exception as e:
        print(f"❌ LỖI NGHIÊM TRỌNG: Không thể ghi log vào ControlManagementDB: {e}")
    finally:
        if log_cursor:
            log_cursor.close()
        if log_conn:
            log_conn.close()

    # --- XỬ LÝ KẾT THÚC (Gửi mail và Exit) ---
    if error_message:
        # BƯỚC 7.2.a GỬI EMAIL LỖI
        print(f"Đã xảy ra lỗi: {error_message}")
        print("Bắt đầu gửi email báo lỗi Transform...")
        try:
            email_cfg = config["email"]
            receiver_list = [email_cfg["receiver"]]
            subject = f"[ETL LỖI] Transform thất bại cho ngày {date_to_process}"
            body = (
                f"Quá trình Transform đã thất bại.\n"
                f"Ngày xử lý: {date_to_process}\n\n"
                f"Chi tiết lỗi:\n{error_message}"
            )
            send_email(subject, body, receiver_list)
        except Exception as e:
            print(f"❌ Lỗi khi đang gửi email báo lỗi: {e}")

        sys.exit(1)
