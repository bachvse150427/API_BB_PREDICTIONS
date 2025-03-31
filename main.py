import os
import sys
import subprocess
import time
from datetime import datetime
import logging

# Configure logging
current_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
log_file_path = os.path.join("logs", f"{current_time}.log")
os.makedirs("logs", exist_ok=True)  # Ensure logs directory exists

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_get_mongo_data():
    """Execute the get_mongo_data.py script to fetch data from MongoDB"""
    logger.info("Starting data fetch from MongoDB...")
    try:
        # Run the script as a subprocess
        result = subprocess.run([sys.executable, "get_mongo_data.py"], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        logger.info("Data fetch completed successfully")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running get_mongo_data.py: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def run_api_server():
    """Run the FastAPI server from API.py"""
    logger.info("Starting API server...")
    try:
        # Execute the API.py script
        # This will block until the server is terminated
        os.execv(sys.executable, [sys.executable, "API.py"])
    except Exception as e:
        logger.error(f"Error running API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting application...")
    
    # Step 1: Run get_mongo_data.py to fetch the latest data
    success = run_get_mongo_data()
    
    if not success:
        logger.error("Failed to fetch data from MongoDB. Check if MongoDB is accessible.")
        # Check if we have any existing data to work with
        data_dir = "Get_Data"
        if os.path.exists(data_dir) and any(file.endswith('.csv') for file in os.listdir(data_dir)):
            logger.warning("Using existing data files. Data may not be up to date.")
        else:
            logger.error("No data files available. API will not function correctly.")
            sys.exit(1)
    
    # Step 2: Run the API server
    # Small delay to ensure file writing operations are complete
    time.sleep(1)
    run_api_server() 