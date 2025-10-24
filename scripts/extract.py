import requests
import pandas as pd
from datetime import datetime
import configparser
import os
import sys

# Điều chỉnh đường dẫn cấu hình tùy theo cấu trúc thư mục thực tế của bạn
CONFIG_PATH = '../config/config.ini' 

# Các thuộc tính cũ lấy từ API tổng hợp (dữ liệu chính)
TARGET_CATEGORIES = [
    "GOAL_FOR",
    "ASSIST",
    "SHOT_ON_TARGET",
    "INTERCEPTION_WON",
    "SHOT_ON_TARGET_OUTSIDE",
    "DRIBBLED_WON",
    "AERIAL_WON",
    "PASS_CROSS_WON",
    "DUEL_TACKLE_WON",
    "FOULED",
    "GOALKEEPER_SAVED",
    "GOALKEEPER_CONCEDED",
    "YELLOW_CARD",
    "RED_CARD"
]

# Các thuộc tính mới cần lấy từ 2 API chi tiết (đã loại bỏ các thuộc tính trùng với TARGET_CATEGORIES)
NEW_PLAYER_ATTRIBUTES = [
    # Từ API statistic
    "totalMatchMain", "totalMatchPlayed", "minutesPlayed",
    "goalWithLeftFoot", "goalWithRightFoot", "goalWithHead", "penaltiesGoals",
    "foulCommitted", "block", "clearance", 
    "pass", "ratioGoal", "shot", "ratioGoalInPenaltyArea",
    "ratioGoalOutsidePenaltyArea", "ratioShotOnTarget", "duelWon", 
    "imgUrl", "isGK",
    
    # Từ API overview
    "positionShortName", "teamLogo", "rating", "idMainPosition", "age",
    "teamId", "placeOfOrigin", "dateOfBirth", "height", "weight",
    "dominantFoot", "jerseyNo", "dateStart", "teamName", "position"
]


def load_config(config_file=CONFIG_PATH):
    """Tải file cấu hình."""
    config = configparser.ConfigParser()
    
    # Giả định file config nằm ở ../config/config.ini
    config_path_abs = os.path.abspath(config_file)
    if not os.path.exists(config_path_abs):
        print(f"Lỗi: Không tìm thấy file cấu hình tại {config_path_abs}")
        sys.exit(1)
        
    config.read(config_path_abs)
    return config


def get_player_ids_and_old_stats(config, update_time_str):
    """
    Bước 1: Lấy danh sách ID cầu thủ duy nhất và các chỉ số cũ từ API tổng hợp.
    """
    base_url = config.get('API_FSTATS', 'url')
    league_id = config.get('API_FSTATS', 'leagueId')
    limit = config.get('API_FSTATS', 'limit')
    API_URL = f"{base_url}?leagueId={league_id}&limit={limit}"
    
    print(f"\n1. Đang lấy danh sách ID và chỉ số cũ từ API: {API_URL}")
    response = requests.get(API_URL)
    response.raise_for_status()
    full_stats = response.json()
    stats_data = full_stats.get('data', full_stats)
    
    all_records = []
    
    for category in TARGET_CATEGORIES:
        if category in stats_data and isinstance(stats_data[category], list):
            for player in stats_data[category]:
                all_records.append({
                    "category": category,
                    "id": player.get("id"),
                    "name": player.get("name"),
                    "result": player.get("result"),
                    "update_time": update_time_str
                })
    
    if not all_records:
        return None, None
        
    df_long = pd.DataFrame(all_records)
    # Chuyển đổi thành định dạng wide cho các chỉ số cũ
    df_old_stats = df_long.pivot(
        index=['id', 'name', 'update_time'],
        columns='category',
        values='result'
    ).reset_index().rename(columns={
        'id': 'Player_ID',
        'name': 'Player_Name',
        'update_time': 'Update_Time'
    }).fillna(0) # Giữ nguyên fillna(0) để khớp với code cũ và chỉ số numeric
    
    # Lấy danh sách ID và Name duy nhất để dùng cho các API chi tiết
    player_list = df_old_stats[['Player_ID', 'Player_Name']].drop_duplicates().reset_index(drop=True)
    
    print(f"-> Tìm thấy {len(player_list)} cầu thủ duy nhất.")
    return player_list, df_old_stats


def get_new_player_details(config, player_list, update_time_str):
    """
    Bước 2: Lặp qua danh sách cầu thủ và gọi 2 API chi tiết để lấy thông tin mới.
    """
    league_id = config.get('API_FSTATS', 'leagueId')
    stat_base_url = config.get('API_FSTATS', 'STATISTIC_BASE_URL')
    overview_base_url = config.get('API_FSTATS', 'OVERVIEW_BASE_URL')
    new_details = []
    
    print("2. Đang lấy dữ liệu chi tiết từ 2 API mới (statistic & overview)...")

    for index, row in player_list.iterrows():
        player_id = row['Player_ID']
        
        player_data = {'Player_ID': player_id, 'Update_Time': update_time_str}
        
        # --- API Statistic ---
        stat_url = f"{stat_base_url}?leagueId={league_id}&playerId={player_id}"
        try:
            stat_res = requests.get(stat_url)
            stat_res.raise_for_status()
            stat_data = stat_res.json().get('player', {})
            
            for key in NEW_PLAYER_ATTRIBUTES:
                # Chỉ lấy các thuộc tính mới có trong API statistic
                if key in stat_data and key not in player_data: 
                    player_data[key] = stat_data[key]
                        
        except requests.exceptions.RequestException as e:
            print(f"Lỗi API Statistic cho ID {player_id}: {e}")
            
        # --- API Overview ---
        overview_url = f"{overview_base_url}?leagueId={league_id}&playerId={player_id}"
        try:
            overview_res = requests.get(overview_url)
            overview_res.raise_for_status()
            overview_data = overview_res.json()
            
            for key in NEW_PLAYER_ATTRIBUTES:
                # Chỉ lấy các thuộc tính mới có trong API overview và chưa có
                if key in overview_data and key not in player_data:
                     player_data[key] = overview_data[key]

        except requests.exceptions.RequestException as e:
            print(f"Lỗi API Overview cho ID {player_id}: {e}")
            
        new_details.append(player_data)
        
    return pd.DataFrame(new_details)


def fetch_and_export_data(config):
    """Hàm chính thực hiện toàn bộ quy trình ETL."""
    now = datetime.now()
    update_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # --- ĐỌC CẤU HÌNH OUTPUT TỪ CONFIG.INI ---
    # 1. Đọc đường dẫn thư mục output từ config
    output_dir = config.get('OUTPUT', 'csv_output_path')
    
    # 2. Đọc tiền tố tên file
    filename_prefix = config.get('OUTPUT', 'FILENAME_PREFIX')
    
    # 3. Tạo tên file
    current_date = now.strftime("%d_%m_%Y")
    base_file_name = f"{filename_prefix}{current_date}_full_stats.csv"
    
    # 4. Tạo đường dẫn file đầy đủ (ví dụ: ../data/staging_...csv)
    file_name = os.path.join(output_dir, base_file_name)
    
    # 5. Tự động tạo thư mục output nếu nó chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)
    # --- KẾT THÚC PHẦN CẬP NHẬT ---

    try:
        # Bước 1: Lấy danh sách ID và chỉ số cũ
        player_list, df_old_stats = get_player_ids_and_old_stats(config, update_time_str)
        
        if player_list is None:
            print("Không có dữ liệu cầu thủ hợp lệ từ API tổng hợp.")
            return

        # Bước 2: Lấy dữ liệu chi tiết mới
        df_new_stats = get_new_player_details(config, player_list, update_time_str)
        
        # Bước 3: Hợp nhất dữ liệu
        print("3. Đang hợp nhất dữ liệu...")
        
        # Merge df_old_stats (chứa Player_Name) và df_new_stats
        df_final = pd.merge(
            df_old_stats, 
            df_new_stats, 
            on=['Player_ID', 'Update_Time'], 
            how='left'
        )
        
        # Làm sạch và định dạng cuối
        df_final.columns = [col.replace(' ', '_') for col in df_final.columns]
        
        numeric_cols = df_final.select_dtypes(include=['number']).columns
        df_final[numeric_cols] = df_final[numeric_cols].fillna(0)


        # Bước 4: Xuất ra CSV (sử dụng đường dẫn đầy đủ 'file_name')
        df_final.to_csv(file_name, index=False, encoding='utf-8')
        
        # In ra đường dẫn tuyệt đối để bạn dễ kiểm tra
        print(f"Hoàn tất trích xuất và hợp nhất dữ liệu. File CSV đã lưu tại: {os.path.abspath(file_name)}")

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API: {e}")
    except Exception as e:
        print(f"Lỗi không xác định trong quá trình xử lý: {e}")
        
if __name__ == "__main__":
    config = load_config()
    fetch_and_export_data(config)