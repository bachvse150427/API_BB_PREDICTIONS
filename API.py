import os
import glob
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel
import logging
import traceback  # Thêm để xem chi tiết lỗi

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Data API",
    description="API to get latest stock predictions data",
    version="1.0.0"
)

# Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount thư mục static
app.mount("/static", StaticFiles(directory="static"), name="static")

class StockData(BaseModel):
    # Định nghĩa model dữ liệu trả về
    date: str
    symbol: str
    prediction: float
    # Thêm các trường khác tùy theo dữ liệu CSV của bạn

# Thêm model Pydantic để validate input
class StockQuery(BaseModel):
    ticker: str
    model: str
    month_year: str

def get_latest_csv():
    try:
        # Lấy đường dẫn tuyệt đối của thư mục hiện tại
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "Get_Data")
        
        # Kiểm tra thư mục tồn tại
        if not os.path.exists(data_dir):
            logger.error(f"Directory not found: {data_dir}")
            raise FileNotFoundError(f"Directory not found: {data_dir}")
        
        # Tìm tất cả file CSV
        pattern = os.path.join(data_dir, "mongodb_data_*.csv")
        csv_files = glob.glob(pattern)
        
        logger.info(f"Found CSV files: {csv_files}")
        
        if not csv_files:
            raise FileNotFoundError("No CSV files found")
        
        # Lấy file mới nhất
        latest_file = max(csv_files, key=os.path.getctime)
        logger.info(f"Latest CSV file: {latest_file}")
        
        # Kiểm tra file có tồn tại và có thể đọc được
        if not os.path.isfile(latest_file):
            raise FileNotFoundError(f"File not found: {latest_file}")
            
        # Thử đọc file để kiểm tra
        df = pd.read_csv(latest_file)
        logger.info(f"File loaded successfully. Columns: {df.columns.tolist()}")
        
        return latest_file
    except Exception as e:
        logger.error(f"Error in get_latest_csv: {str(e)}")
        logger.error(traceback.format_exc())  # In ra stack trace đầy đủ
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')
##1/
@app.get("/test")
async def test_endpoint():
    try:
        latest_file = get_latest_csv()
        df = pd.read_csv(latest_file)
        return {
            "status": "success",
            "file": latest_file,
            "rows": len(df),
            "columns": list(df.columns)
        }
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

##2#
@app.get("/stock-prediction")
def get_stock_prediction(
    ticker: str = Query(..., description="Stock ticker symbol"),
    model: str = Query(..., description="Model name"),
    month_year: str = Query(..., description="Month-Year format (e.g., 2024-03)")
):
    try:
        latest_file = get_latest_csv()
        logger.info(f"Reading file for ticker {ticker}, model {model}, month-year {month_year}")
        
        # Đọc dữ liệu từ CSV
        df = pd.read_csv(latest_file)
        logger.info(f"Data loaded. Columns: {df.columns.tolist()}")
        
        # Kiểm tra các cột bắt buộc
        required_columns = ['Ticker', 'Model', 'Month-Year', 'Index', 'Actual', 
                          'Prediction', 'Prob_Class_0', 'Prob_Class_1', 'Correct']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing columns in CSV: {missing_columns}")
        
        # Lọc dữ liệu theo các điều kiện
        filtered_df = df[
            (df['Ticker'] == ticker) & 
            (df['Model'] == model) & 
            (df['Month-Year'] == month_year)
        ]
        
        if filtered_df.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"No data found for Ticker={ticker}, Model={model}, Month-Year={month_year}"
            )
        
        # Chỉ lấy các cột cần thiết
        result_df = filtered_df[required_columns]
        
        # Tính toán thống kê
        total_predictions = len(result_df)
        correct_predictions = result_df['Correct'].sum()
        accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        return JSONResponse(
            content={
                "status": "success",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query_params": {
                    "ticker": ticker,
                    "model": model,
                    "month_year": month_year
                },
                "statistics": {
                    "total_predictions": total_predictions,
                    "correct_predictions": int(correct_predictions),
                    "accuracy": float(accuracy)
                },
                "data": result_df.to_dict('records')
            }
        )
    except Exception as e:
        logger.error(f"Error in get_stock_prediction: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

##3# Thêm endpoint để lấy danh sách các giá trị unique cho mỗi trường
@app.get("/available-filters")
def get_available_filters():
    try:
        latest_file = get_latest_csv()
        df = pd.read_csv(latest_file)
        
        return {
            "tickers": sorted(df['Ticker'].unique().tolist()),
            "models": sorted(df['Model'].unique().tolist()),
            "month_years": sorted(df['Month-Year'].unique().tolist())
        }
    except Exception as e:
        logger.error(f"Error in get_available_filters: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")