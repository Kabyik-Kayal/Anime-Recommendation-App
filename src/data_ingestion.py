import os
import pandas as pd
from google.cloud import storage

from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *
from utils.common_functions import read_yaml

logger = get_logger(__name__)

class DataIngestion:
    def __init__(self, config):
        self.config = config["data_ingestion"]
        self.bucket_name = self.config["bucket_name"]
        self.file_names = self.config["bucket_file_names"]

        os.makedirs(RAW_DIR, exist_ok=True)

        logger.info(f"Data Ingestion initialized from GCP Bucket : {self.bucket_name}.")
    
    def download_csv_from_gcp(self):
        """
        Download CSV files from GCP bucket and save them to the local directory.
        """
        try:
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)

            for file in self.file_names:
                local_file_path = os.path.join(RAW_DIR, file)
                blob = bucket.blob(file)
                blob.download_to_filename(local_file_path)
                logger.info(f"Downloaded {file} from GCP bucket to {local_file_path}.")
        
        except Exception as e:
            logger.error(f"Error downloading files from GCP: {e}")
            raise CustomException("Failed to download the data", e)
        
    def run_data_ingestion(self):
        """
        Run the data ingestion process.
        """
        try:
            logger.info("Data ingestion Step Started.")
            self.download_csv_from_gcp()
            logger.info("Data ingestion Step Completed.")

        except Exception as e:
            logger.error(f"Error during data ingestion: {str(e)}")
        
        finally:
            logger.info("Data ingestion process finished.")

if __name__ == "__main__":
    
    data_ingestion = DataIngestion(read_yaml(CONFIG_PATH))
    data_ingestion.run_data_ingestion()
