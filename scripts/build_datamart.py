import os
import datetime
import sys
import argparse
import traceback
from configparser import ConfigParser
import mysql.connector

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_utils import connect_db, insert_log, update_log_status
from utils.email_utils import send_email

parser = argparse.ArgumentParser(description="Build DataMart")
parser.add_argument('--date', type=str, help='Ngày chạy Datamart (YYYY-MM-DD), mặc định hôm nay')
args = parser.parse_args()

# Nếu không nhập thì lấy ngày hôm nay
run_date = args.date or datetime.datetime.now().strftime("%Y-%m-%d")
print(f"Ngày chạy Datamart: {run_date}")

def get_config(config_path="config/config.ini"):
    """Đọc file cấu hình."""
    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', config_path))
    return config

def connect_dwh(config):
    """Kết nối tới DataWarehouseDB."""
    db_cfg = config["databaseDataWarehouseDB"]
    conn = mysql.connector.connect(
        host=db_cfg["host"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        database=db_cfg["database"],
        port=int(db_cfg.get("port", 3306))
    )
    return conn, conn.cursor(dictionary=True)

def connect_datamart(config):
    """Kết nối tới Player_Performance_Mart."""
    db_cfg = config["databasePlayer_Performance_Mart"]
    conn = mysql.connector.connect(
        host=db_cfg["host"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        database=db_cfg["database"],
        port=int(db_cfg.get("port", 3306))
    )
    return conn, conn.cursor(dictionary=True)

def run_datamart_build():
    job_name = "Build_Player_Performance_Mart"
    start_time = datetime.datetime.now()
    log_id = None
    
    conn_control = None
    cursor_control = None
    conn_dwh = None
    cursor_dwh = None
    conn_dm = None
    cursor_dm = None
    
    receivers = []
    
    preceding_job_name = "load_to_datawarehouse" 

    try:
        # 9.1. Đọc file config
        config = get_config()
        email_config = config["email"]
        receivers = [x.strip() for x in email_config["receiver"].split(",")]

        # 9.2. Kết nối ControlDB và bắt đầu ghi log
        conn_control, cursor_control = connect_db()
        log_id = insert_log(cursor_control, job_name, start_time, "RUNNING")
        conn_control.commit()
        print(f"Bắt đầu job: {job_name} lúc {start_time}")

        # # 9.2.1. Kiểm tra log của job (load)
        # print(f"Đang kiểm tra trạng thái job '{preceding_job_name}'...")
        
        # # 9.2.2. Lấy ngày hiện tại theo múi giờ
        # today_date = start_time.strftime('%Y-%m-%d')

        # check_sql = """
        #     SELECT 1 FROM log_history
        #     WHERE job_name = %s
        #     AND status = 'SUCCESS'
        #     AND DATE(end_time) = %s
        #     LIMIT 1
        # """
        # cursor_control.execute(check_sql, (preceding_job_name, today_date))
        
        # if not cursor_control.fetchone():
        #     # Nếu không tìm thấy log SUCCESS hôm nay -> Dừng lại và báo lỗi
        #     error_msg = f"Job truoc '{preceding_job_name}' chua chay thanh cong hom nay ({today_date})."
        #     print(f"{error_msg}")
        #     raise Exception(error_msg)
            
        # print(f"Job '{preceding_job_name}' đã chạy thành công. Tiếp tục...")


        # 9.3. Kết nối DWH (Nguồn) và DataMart (Đích)
        print("Đang kết nối tới DataWarehouse và DataMart...")
        conn_dwh, cursor_dwh = connect_dwh(config)
        conn_dm, cursor_dm = connect_datamart(config)
        print("Kết nối DWH và DataMart thành công.")

        
        # 9.4. TRÍCH XUẤT (E) và BIẾN ĐỔI (T) từ DataWarehouse
        # *** LƯU Ý: Câu SQL này phải JOIN 3 bảng trong DWH
        #     (fact_performance, dim_player, dim_date)
        #     để lấy được dữ liệu nạp vào 2 bảng Mart của bạn.
        
        print("Đang thực thi truy vấn (E)xtract & (T)ransform từ DWH...")
        
        # --- Bảng 1: top_player_ranking_mart ---
        #9.4.1 (Lấy Top 10 cầu thủ theo 'metric_value' loại 'goals')
        sql_query_1 = """
            SELECT 
                p.player_name, 
                p.team_name, 
                f.metric_type, 
                f.metric_value, 
                f.rating, 
                d.api_date, 
                d.month_name
            FROM 
                fact_performance f
            JOIN 
                dim_player p ON f.player_key = p.player_key
            JOIN 
                dim_date d ON f.date_key = d.date_key
            WHERE f.metric_type IN ('GOAL_FOR', 'ASSIST')
            ORDER BY 
                f.metric_value DESC
            LIMIT 10;
        """
        cursor_dwh.execute(sql_query_1)
        data_to_load_1 = cursor_dwh.fetchall()
        print(f"Trích xuất {len(data_to_load_1)} dòng cho 'top_player_ranking_mart'.")
        
        # --- Bảng 2: player_performance_agg_mart ---
        #9.4.2 (Lấy tất cả dữ liệu đã join)
        sql_query_2 = """
SELECT 
    p.player_key, p.player_id, p.player_name, p.team_id, p.team_name, 
    p.nationality, p.position, p.age, p.height_cm, p.weight_kg, p.dominant_foot,
    d.date_key, d.api_date, d.year, d.quarter, d.month, d.month_name,
    f.metric_type,
    SUM(f.metric_value) AS metric_value,
    SUM(f.duelWon) AS duelWon,
    AVG(f.passSuccess) AS passSuccess,
    SUM(f.assist) AS assist,
    SUM(f.shotOnTarget) AS shotOnTarget,
    AVG(f.rating) AS rating
FROM fact_performance f
JOIN dim_player p ON f.player_key = p.player_key
JOIN dim_date d ON f.date_key = d.date_key
WHERE p.is_current = 1
GROUP BY
    p.player_key, p.player_id, p.player_name, p.team_id, p.team_name,
    p.nationality, p.position, p.age, p.height_cm, p.weight_kg, p.dominant_foot,
    d.date_key, d.api_date, d.year, d.quarter, d.month, d.month_name,
    f.metric_type;
"""

        cursor_dwh.execute(sql_query_2)
        data_to_load_2 = cursor_dwh.fetchall()
        print(f"Trích xuất {len(data_to_load_2)} dòng cho 'player_performance_agg_mart'.")
        
        if not data_to_load_1 and not data_to_load_2:
            print("⚠️ Không có dữ liệu mới từ DWH. Dừng job.")
            raise Exception("Không có dữ liệu nguồn từ DataWarehouseDB.")


        # 9.5. TẢI (L) vào DataMart (Chiến lược TRUNCATE và LOAD)
        
        # 9.5.1 Tải Bảng 1: top_player_ranking_mart
        print("Đang Tải (L)oad vào 'top_player_ranking_mart'...")
        cursor_dm.execute("TRUNCATE TABLE top_player_ranking_mart") 
        
        insert_sql_1 = """
            INSERT INTO top_player_ranking_mart (
                player_name, team_name, metric_type, metric_value, 
                rating, api_date, month_name
            ) VALUES (
                %(player_name)s, %(team_name)s, %(metric_type)s, %(metric_value)s, 
                %(rating)s, %(api_date)s, %(month_name)s
            )
        """
        if data_to_load_1:
            cursor_dm.executemany(insert_sql_1, data_to_load_1)
            conn_dm.commit()
            print(f"Đã nạp {cursor_dm.rowcount} dòng vào 'top_player_ranking_mart'.")

        
        # 9.5.2. Tải Bảng 2: player_performance_agg_mart
        print("Đang Tải (L)oad vào 'player_performance_agg_mart'...")
        cursor_dm.execute("TRUNCATE TABLE player_performance_agg_mart") 

        insert_sql_2 = """
            INSERT INTO player_performance_agg_mart (
                player_key, player_id, player_name, team_id, team_name, nationality, 
                position, age, height_cm, weight_kg, dominant_foot, date_key, 
                api_date, year, quarter, month, month_name, metric_type, 
                metric_value, duelWon, passSuccess, assist, shotOnTarget, rating
            ) VALUES (
                %(player_key)s, %(player_id)s, %(player_name)s, %(team_id)s, %(team_name)s, %(nationality)s, 
                %(position)s, %(age)s, %(height_cm)s, %(weight_kg)s, %(dominant_foot)s, %(date_key)s, 
                %(api_date)s, %(year)s, %(quarter)s, %(month)s, %(month_name)s, %(metric_type)s, 
                %(metric_value)s, %(duelWon)s, %(passSuccess)s, %(assist)s, %(shotOnTarget)s, %(rating)s
            )
        """
        if data_to_load_2:
            cursor_dm.executemany(insert_sql_2, data_to_load_2)
            conn_dm.commit()
            print(f"Đã nạp {cursor_dm.rowcount} dòng vào 'player_performance_agg_mart'.")

        records_processed = len(data_to_load_1) + len(data_to_load_2)

        # 9.6. Cập nhật log SUCCESS
        end_time = datetime.datetime.now()
        update_log_status(cursor_control, log_id, "SUCCESS", end_time, records_processed)
        conn_control.commit()
        print("Job hoàn tất thành công!")

        # 9.7. Gửi email THÀNH CÔNG
        send_email(
            subject=f"[DATAMART SUCCESS] {job_name} Completed",
            body=f"Job {job_name} đã chạy thành công \n"
                 f"Thời gian: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                 f"Số dòng đã xử lý: {records_processed}",
            to_list=receivers
        )

    except Exception as e:
        # 9.8. Xử lý lỗi
        print(f"Đã xảy ra lỗi: {e}")
        print(traceback.format_exc()) # In chi tiết lỗi
        end_time = datetime.datetime.now()
        
        # 9.8.1. Cập nhật log THẤT BẠI
        if conn_control and log_id:
            update_log_status(cursor_control, log_id, "FAILED", end_time, error_message=str(e))
            conn_control.commit()
        
        # 9.8.2. Gửi email THẤT BẠI
        if receivers:
            send_email(
                subject=f"[DATAMART FAILED] {job_name} FAILED",
                body=f"Job {job_name} đã chạy không thành công \n"
                     f"Thời gian: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"Lỗi: {e}",
                to_list=receivers
            )

    finally:
        # 9.9. Đóng tất cả các kết nối
        print("Đóng tất cả kết nối...")
        if cursor_control: cursor_control.close()
        if conn_control: conn_control.close()
        if cursor_dwh: cursor_dwh.close()
        if conn_dwh: conn_dwh.close()
        if cursor_dm: cursor_dm.close()
        if conn_dm: conn_dm.close()

# ----- Chạy script -----
if __name__ == "__main__":
    run_datamart_build()