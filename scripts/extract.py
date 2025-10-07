import cloudscraper
import configparser
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_config():
    # Đọc file cấu hình từ thư mục config/
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    return config

def extract_data():
    config = get_config()
    api_url = config['API']['base_url']
    api_params = config['API']['params']

    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(f"{api_url}?{api_params}")
        response.raise_for_status()
        data = response.json()
        
        match_list = data.get('data', {}).get('listMatch', []) 
        logging.info(f"Extract thành công {len(match_list)} trận đấu.")
        return match_list
        
    except Exception as e:
        logging.error(f"Lỗi khi gọi API: {e}")
        return None