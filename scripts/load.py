import mysql.connector
import datetime
import configparser
import os
import sys
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === 8.0 Xác định ROOT PROJECT để đọc config từ đường dẫn tương đối ===
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# === Hàm phụ: kết nối tới MySQL theo từng section trong config.ini ===
def connect_mysql(section_name, config):
    db_cfg = config[section_name]
    return mysql.connector.connect(
        host=db_cfg.get("host"),
        user=db_cfg.get("user"),
        password=db_cfg.get("password"),
        database=db_cfg.get("database"),
        port=db_cfg.get("port", 3306),
    )

# === Hàm phụ: gửi email thông báo trạng thái job ===
def send_email(config, subject, body):
    try:
        email_cfg = config["email"]
        sender = email_cfg["sender"]
        receiver = email_cfg["receiver"]
        password = email_cfg["password"]
        smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
        smtp_port = int(email_cfg.get("smtp_port", 587))

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        print(f"📧 Email đã gửi tới {receiver}")
    except Exception as e:
        print(f"⚠️ Gửi email thất bại: {e}")

# === Hàm phụ: sinh khóa ngày (date_key) theo chuẩn DIM_DATE ===
def generate_date_key(date_obj):
    return date_obj.strftime("%Y%m%d")


# ================================================================
# ======================== 8. LOAD TO DWH =========================
# ================================================================
def load_to_datawarehouse(config, data_date):
    start_time = datetime.datetime.now()
    print(f"🚀 Bắt đầu LOAD dữ liệu cho ngày {data_date}...")

    staging_conn = dw_conn = control_conn = None
    staging_cur = dw_cur = control_cur = None
    records_loaded = 0
    status = "RUNNING"
    error_msg = None
    log_id = None

    try:
        # === 8.1.1 Kết nối tới ControlManagementDB ===
        control_conn = connect_mysql("databaseControlManagementDB", config)
        control_cur = control_conn.cursor()

        # === 8.1.2 Kiểm tra job Transform (7.x) đã chạy thành công chưa ===
        # Nếu transform chưa SUCCESS → STOP load
        control_cur.execute("""
            SELECT status 
            FROM log_history 
            WHERE job_name = 'transform_staging_load'
            ORDER BY start_time DESC 
            LIMIT 1
        """)
        result = control_cur.fetchone()

        if not result or result[0] != "SUCCESS":
            raise Exception("Job transform_to_staging chưa SUCCESS — dừng LOAD.")
        print("✅ Kiểm tra job Transform: SUCCESS — cho phép LOAD.")

        # === 8.1.3 Ghi log RUNNING vào ControlManagementDB ===
        control_cur.execute(
            """
            INSERT INTO log_history (job_name, start_time, status, records_processed)
            VALUES (%s, %s, %s, %s)
            """,
            ("load_to_datawarehouse", start_time, "RUNNING", 0),
        )
        log_id = control_cur.lastrowid
        control_conn.commit()
        print("🟢 Ghi log trạng thái RUNNING...")

        # === 8.2 Kết nối tới Staging & Data Warehouse ===
        staging_conn = connect_mysql("databasePerformance_Staging", config)
        dw_conn = connect_mysql("databaseDataWarehouseDB", config)
        staging_cur = staging_conn.cursor(dictionary=True)
        dw_cur = dw_conn.cursor(dictionary=True)
        print("✅ Đã kết nối tới Staging, Data Warehouse và Control DB")

        # === 8.3 Đọc dữ liệu staging của ngày data_date ===
        staging_cur.execute("SELECT * FROM player_staging WHERE api_date = %s", (data_date,))
        players = staging_cur.fetchall()
        if not players:
            raise Exception(f"Không có dữ liệu staging cho ngày {data_date}")
        print(f"📦 Đã đọc {len(players)} bản ghi từ player_staging")

        # === 8.4 Kiểm tra / Insert dim_date nếu chưa tồn tại ===
        date_obj = datetime.datetime.strptime(data_date, "%Y-%m-%d").date()
        date_key = generate_date_key(date_obj)

        dw_cur.execute("SELECT date_key FROM dim_date WHERE date_key = %s", (date_key,))
        if not dw_cur.fetchone():
            # === 8.4.1 Insert DIM_DATE mới ===
            dw_cur.execute(
                """
                INSERT INTO dim_date (date_key, api_date, full_date, year, quarter, month, day, 
                                      day_of_week, day_name, month_name, is_weekend, load_batch)
                VALUES (%s,%s,%s,%s,QUARTER(%s),MONTH(%s),DAY(%s),
                        DAYOFWEEK(%s),DAYNAME(%s),MONTHNAME(%s),
                        CASE WHEN DAYOFWEEK(%s) IN (1,7) THEN 1 ELSE 0 END, %s)
                """,
                (
                    date_key, data_date, data_date, date_obj.year,
                    data_date, data_date, data_date,
                    data_date, data_date, data_date,
                    data_date, f"batch_{date_key}"
                ),
            )
            print(f"📅 Thêm mới dim_date: {date_key}")

            # === 8.4.2 Nếu có dữ liệu cũ trong fact_performance → xóa ===
            print(f"🧹 Kiểm tra dữ liệu cũ trong fact_performance cho ngày {date_key}...")
            dw_cur.execute("SELECT COUNT(*) AS cnt FROM fact_performance WHERE date_key = %s", (date_key,))
            existing_count = dw_cur.fetchone()["cnt"]
            if existing_count > 0:
                print(f"⚠️ Phát hiện {existing_count} bản ghi cũ → xóa trước khi nạp mới.")
                dw_cur.execute("DELETE FROM fact_performance WHERE date_key = %s", (date_key,))
                dw_conn.commit()
            else:
                print("✅ Không có dữ liệu cũ cần xóa.")

        # === 8.5 Load DIM_PLAYER và FACT_PERFORMANCE ===
        for p in players:

            # === 8.5.1 Kiểm tra player đã tồn tại chưa ===
            dw_cur.execute("SELECT * FROM dim_player WHERE player_id = %s AND is_current = 1", (p["player_id"],))
            current_player = dw_cur.fetchone()

            if not current_player:
                # === 8.5.2 Thêm mới DIM_PLAYER ===
                dw_cur.execute(
                    """
                    INSERT INTO dim_player (
                        player_id, player_name, team_id, team_name, nationality, position,
                        age, height_cm, weight_kg, dominant_foot, is_current, load_batch
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s)
                    """,
                    (
                        p["player_id"], p["player_name"], p["team_id"], p["team_name"],
                        p["nationality"], p["position"], p["age"], p["height"],
                        p["weight"], p["dominant_foot"], f"batch_{date_key}"
                    ),
                )
                dw_cur.execute("SELECT LAST_INSERT_ID() AS player_key")
                player_key = dw_cur.fetchone()["player_key"]
            else:
                # === 8.5.3 Nếu player đã tồn tại → lấy player_key ===
                player_key = current_player["player_key"]

            # === 8.5.4 Insert FACT_PERFORMANCE ===
            dw_cur.execute(
                """
                INSERT INTO fact_performance (
                    player_key, date_key, metric_type, metric_value, duelWon,
                    passSuccess, assist, shotOnTarget, rating, load_batch
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    player_key, date_key, p["metric_type"], p["metric_value"],
                    p["duelWon"], p["passSuccess"], p["assist"], p["shotOnTarget"],
                    p["rating"], f"batch_{date_key}"
                ),
            )
            records_loaded += 1

        # === 8.6 Commit toàn bộ dữ liệu vào DW ===
        dw_conn.commit()
        status = "SUCCESS"
        print(f"✅ Đã load {records_loaded} bản ghi vào fact_performance")

    # === Bắt lỗi ===
    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        print(f"❌ Lỗi LOAD: {error_msg}")
        if dw_conn:
            dw_conn.rollback()

    finally:
        # === 8.8 Cập nhật LOG (SUCCESS / FAILED) ===
        end_time = datetime.datetime.now()
        if control_conn and log_id:
            control_cur.execute(
                """
                UPDATE log_history
                SET end_time = %s, status = %s, records_processed = %s, error_message = %s
                WHERE id = %s
                """,
                (end_time, status, records_loaded, error_msg, log_id),
            )
            control_conn.commit()
            print(f"📋 Cập nhật log {status} vào ControlManagementDB.")

        # === 8.9 Gửi email thông báo kết quả ===
        subject = f"[ETL LOAD] {status} - {data_date}"
        body = f"""
        Job: load_to_datawarehouse
        Date: {data_date}
        Status: {status}
        Records Loaded: {records_loaded}
        Start Time: {start_time}
        End Time: {end_time}
        Error: {error_msg if error_msg else 'None'}
        """
        send_email(config, subject, body)

        # === 8.10 Đóng kết nối ===
        for c in [staging_cur, dw_cur, control_cur]:
            if c: c.close()
        for conn in [staging_conn, dw_conn, control_conn]:
            if conn and conn.is_connected():
                conn.close()

    # === 8.11 Trả về kết quả cho Scheduler hoặc người gọi ===
    return status, error_msg, records_loaded

# === Hàm phụ: gửi email thông báo trạng thái job ===
def send_email(config, subject, body):
    try:
        email_cfg = config["email"]
        sender = email_cfg["sender"]
        receiver = email_cfg["receiver"]
        password = email_cfg["password"]
        smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
        smtp_port = int(email_cfg.get("smtp_port", 587))

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        print(f"📧 Email đã gửi tới {receiver}")

    except Exception as e:
        print(f"⚠️ Gửi email thất bại: {e}")



# ================================================================
# ======================== ENTRY POINT ============================
# ================================================================
if __name__ == "__main__":
    # === 8. Đọc config.ini ===
    config = configparser.ConfigParser()
    config.read(os.path.join(PROJECT_ROOT, "config", "config_load.ini"))

    # === 8.1 Lấy timezone từ config ,tham số ngày từ scheduler ===
    timezone_name = (
        config["general"]["timezone"]
        if config.has_section("general") and "timezone" in config["general"]
        else "Asia/Ho_Chi_Minh"
    )
    tz = pytz.timezone(timezone_name)

    if len(sys.argv) > 1:
        data_date = sys.argv[1]
        print(f"📅 Nhận tham số ngày: {data_date}")
    else:
        data_date = datetime.datetime.now(tz).strftime("%Y-%m-%d")
        print(f"📅 Không có tham số, dùng ngày hiện tại: {data_date}")

    load_to_datawarehouse(config, data_date)
