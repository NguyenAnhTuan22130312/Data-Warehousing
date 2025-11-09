import requests, csv, datetime, json
import configparser
import sys, os
import mysql.connector
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_utils import connect_db, insert_log_history,insert_log_new
import argparse


# 6. Đọc  cấu hình từ config và lấy thông tin database ControlManagementDB
config = configparser.ConfigParser()
config.read(os.path.join('config', 'config.ini'))
# Lấy thông tin database ControlManagementDB
db_config = config['databaseControlManagementDB']
#Kết nối DB
conn  = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",        
    database="ControlManagementDB"   
)
cursor = conn.cursor(dictionary=True)
print("✅ Kết nối thành công đến cơ sở dữ liệu:", db_config.get('database'))


# 6.1. Thiết lập ngày chạy ETL tự động
# Nhận tham số ngày
parser = argparse.ArgumentParser(description="Extract Player Data")
parser.add_argument('--date', type=str, required=True, help='Ngày dữ liệu (YYYY-MM-DD)')
args = parser.parse_args()
data_date = args.date
print(f"Ngày chạy ETL tự động: {data_date}")

# 6.2. Lấy danh sách API có trạng thái active từ bảng DataSource
cursor.execute("SELECT * FROM DataSource WHERE Is_Active=1")
apis = cursor.fetchall()

#Có API hay không ?
#không
if not apis:
    error_message = "❌ Không lấy được danh sách API"
    print(error_message)
    #Lưu lại log với trạng thái FAILED
    end_time = datetime.datetime.now()
    created_at = datetime.datetime.now()
    insert_log_new(cursor, "GET_ALL_API", end_time, error_message, created_at,  "FAILED")
    conn.commit()

    # dừng ETL
    raise Exception(error_message)

#có
#6.3. Gọi API với enpoint có top_5_player trong DataSource
api1 = next((a for a in apis if 'top5-player' in a['Endpoint']), None)

#API có tồn tại không ?
#Không
if not api1:
    error_message = "❌ Không tìm thấy API top5-player trong DataSource"
    print(error_message)
    #Lưu lại log với trạng thái FAILD
    end_time = datetime.datetime.now()
    created_at = datetime.datetime.now()
    insert_log_new(cursor, "CALL_API_1", end_time, error_message, created_at,  "FAILED")
    conn.commit()

    # dừng ETL
    raise Exception(error_message)

#Có
params = json.loads(api1['Params']) if api1['Params'] else {}
res = requests.get(f"{api1['Base_URL']}{api1['Endpoint']}", params=params)
res.raise_for_status()  # ném lỗi nếu HTTP != 200
data = res.json()

# 6.4 Chuyển dữ liệu metric thành list
player_list = []
for metric, players in data.items():
    for p in players:
        player_list.append({
            'player_id': p.get('id'),
            'player_name': p.get('name'),
            'metric_type': metric,
            'metric_value': p.get('result')
        })


#6.5 Gọi API 2 và 3 đã thiết lập trong bảng DataSource 
api2 = next((a for a in apis if 'overview' in a['Endpoint']), None)
api3 = next((a for a in apis if 'performance' in a['Endpoint']), None)

# API có tồn tại không ?
#Không
if not api2 or not api3:
    error_message = "❌ Thiếu API overview hoặc performance trong DataSource"
    print(error_message)
    # 6.5.1 Lưu lại log với trạng thái FAILD
    end_time = datetime.datetime.now()
    created_at = datetime.datetime.now()
    insert_log_new(cursor, "CALL_API_2_OR_3", end_time, error_message, created_at,  "FAILED")
    conn.commit()

    # dừng ETL
    raise Exception(error_message)

final_rows = []

#Có
#6.5.2 Lấy dữ liệu trả về từ 2 API 
for p in player_list:
    pid = p['player_id']

    # Gọi API overview
    overview = requests.get(
        f"{api2['Base_URL']}{api2['Endpoint']}",
        params={"leagueId": 28, "playerId": pid}
    ).json()

    # Gọi API performance
    perf = requests.get(
        f"{api3['Base_URL']}{api3['Endpoint']}",
        params={"leagueId": 28, "playerId": pid}
    ).json()

    perf_player = perf.get('player', {})

    final_rows.append({
        'player_id': pid,
        'player_name': overview.get('fullName', p['player_name']),
        'team_id': overview.get('teamId'),
        'team_name': overview.get('teamName'),
        'nationality': overview.get('placeOfOrigin'),
        'position': overview.get('position'),
        'age': overview.get('age'),
        'height': overview.get('height'),
        'weight': overview.get('weight'),
        'dominant_foot': overview.get('dominantFoot'),
        'rating': overview.get('rating'),
        'metric_type': p['metric_type'],
        'metric_value': p['metric_value'],
        'duelWon': perf_player.get('duelWon'),
        'passSuccess': perf_player.get('passSuccess'),
        'assist': perf_player.get('assist'),
        'shotOnTarget': perf_player.get('shotOnTarget'),
        'api_date': data_date,
        'extract_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


#6.6 Khởi tạo tên file đầu ra cho file csv
output_dir = os.path.join('data')
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f"staging_player_stats_{data_date}.csv")


try:
        #6.7 Chèn dữ liệu từ kết quả của 3 API vào file CSV
        fieldnames = list(final_rows[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_rows)
        print(f"✅ Extracted {len(final_rows)} records → {output_file}")
        
        #6.7.1 Lưu lại log với trạng thái SUCCESS
        insert_log_history(cursor, "extract_player_stats_top5", api1['Source_ID'], "SUCCESS", len(player_list))
        insert_log_history(cursor, "extract_player_stats_overview", api2['Source_ID'], "SUCCESS", len(player_list))
        insert_log_history(cursor, "extract_player_stats_performance", api3['Source_ID'], "SUCCESS", len(player_list))

        conn.commit()

except Exception as e:
        #6.7.2 Lưu lại log với trạng thái FAILED
    insert_log_history(cursor, "extract_player_stats", api1['Source_ID'], "FAILED", 0, str(e))
    conn.commit()

# Đóng kết nối
cursor.close()
conn.close()
