import os
import pandas as pd
from src.logger import get_logger
from src.custom_exception import CustomException
import yaml

logger = get_logger(__name__)

def read_yaml(file_path):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file - {file_path} - does not exist.")
        
        with open(file_path, 'r') as yaml_file:
            config = yaml.safe_load(yaml_file)
            logger.info(f"YAML file - {file_path} - loaded successfully.")
        
        return config

    except Exception as e:
        logger.error(f"Error occurred while reading the YAML file - {file_path}")
        raise CustomException("Failed to read the YAML file", e)
