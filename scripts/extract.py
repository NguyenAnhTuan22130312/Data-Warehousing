import requests
import pandas as pd
from datetime import datetime
import configparser
import os
import sys

CONFIG_PATH = '../config/config.ini' 

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

def load_config(config_file=CONFIG_PATH):
    config = configparser.ConfigParser()
    
    if not os.path.exists(config_file):
        sys.exit(1)
        
    config.read(config_file)
    return config

def fetch_and_export_data(config):
    try:
        # 1. Đọc và xây dựng URL từ section API_FSTATS
        base_url = config.get('API_FSTATS', 'url') 
        league_id = config.get('API_FSTATS', 'leagueId')
        limit = config.get('API_FSTATS', 'limit')

        # Lấy thời điểm hiện tại (Timestamp)
        now = datetime.now()
        
        filename_prefix = config.get('OUTPUT', 'FILENAME_PREFIX')
        
        API_URL = f"{base_url}?leagueId={league_id}&limit={limit}"
        
        # 2. Định dạng tên file
        current_date = datetime.now().strftime("%d_%m_%Y") 
        file_name = f"{filename_prefix}{current_date}.csv"
        update_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Đang kết nối tới API: {API_URL}")
        
        # 3. Gọi API
        response = requests.get(API_URL)
        response.raise_for_status() 

        full_stats = response.json()
        
        stats_data = full_stats.get('data', full_stats) 

        all_records = [] 

        for category in TARGET_CATEGORIES:
            if category in stats_data and isinstance(stats_data[category], list):
                player_list = stats_data[category]
                
                for player in player_list:
                    record = {
                        "category": category,
                        "id": player.get("id"),
                        "name": player.get("name"),
                        "result": player.get("result"),
                        "update_time": update_time_str
                    }
                    all_records.append(record)

        if all_records:
            df_long = pd.DataFrame(all_records)
            
            df_wide = df_long.pivot(
                index=['id', 'name', 'update_time'], 
                columns='category', 
                values='result'
            )
            
            df_wide = df_wide.fillna(0).astype(int)
            
            df_wide = df_wide.reset_index().rename(columns={
                'id': 'Player_ID',
                'name': 'Player_Name',
                'update_time': 'Update_Time' 
            })
            
            df_wide.to_csv(file_name, index=False, encoding='utf-8')
            
            print(f"Hoàn tất trích xuất và lọc dữ liệu.")
        else:
            print("Không có dữ liệu hợp lệ nào được trích xuất sau khi lọc.")

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API (Request Error): {e}")
    

if __name__ == "__main__":
    # Tải cấu hình
    config = load_config()
    
    fetch_and_export_data(config)