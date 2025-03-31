import os
import sys
import pandas as pd
from datetime import datetime
import pymongo
from dotenv import load_dotenv
import certifi

from ApiStock.exception.exception import ApiPredictionException
from ApiStock.logging.logger import logging

load_dotenv()
MONGO_DB_URL = os.getenv("MONGO_DB_URL")
ca = certifi.where()

class NetworkDataFetch:
    def __init__(self):
        try:
            self.mongo_client = pymongo.MongoClient(MONGO_DB_URL)
        except Exception as e:
            raise ApiPredictionException(e, sys)

    def get_latest_collection(self, database):
        try:
            db = self.mongo_client[database]
            # Lấy tất cả collections bắt đầu bằng 'Net_Data_'
            collections = [coll for coll in db.list_collection_names() if coll.startswith('Net_Data_')]
            
            # Sắp xếp theo thời gian và lấy collection mới nhất
            if not collections:
                print(f"No collections found starting with 'Net_Data_' in database {database}")
                print(f"Available collections: {db.list_collection_names()}")
                return None
            
            latest_collection = sorted(collections, reverse=True)[0]
            return latest_collection
        except Exception as e:
            raise ApiPredictionException(e, sys)

    def fetch_data_from_mongodb(self, database, collection):
        try:
            db = self.mongo_client[database]
            collection_data = db[collection]
            # Lấy tất cả documents từ collection
            data = list(collection_data.find({}, {'_id': 0}))
            return data
        except Exception as e:
            raise ApiPredictionException(e, sys)

    def save_to_csv(self, data, output_path):
        try:
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            return output_path
        except Exception as e:
            raise ApiPredictionException(e, sys)

if __name__ == '__main__':
    DATABASE = "BACHV_BB_STOCKS"  # Updated to match push_mongo_data.py
    OUTPUT_DIR = "Get_Data"
    
    # Tạo thư mục output nếu chưa tồn tại
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Tạo tên file với timestamp
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"mongodb_data_{current_time}.csv")
    
    network_fetch = NetworkDataFetch()
    
    # Lấy tên collection mới nhất
    latest_collection = network_fetch.get_latest_collection(DATABASE)
    
    if latest_collection is None:
        print("Error: No collections found with the required prefix.")
        sys.exit(1)
        
    print(f"Latest collection: {latest_collection}")
    
    # Lấy dữ liệu từ MongoDB
    data = network_fetch.fetch_data_from_mongodb(DATABASE, latest_collection)
    print(f"Found {len(data)} records")
    
    if len(data) == 0:
        print("Warning: No data found in the collection.")
        sys.exit(0)
    
    # Lưu dữ liệu vào file CSV
    saved_file = network_fetch.save_to_csv(data, output_file)
    print(f"Data saved to: {saved_file}")