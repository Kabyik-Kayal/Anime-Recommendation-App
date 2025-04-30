import os
from src.data_processing import DataProcessor
from src.model_training import ModelTraining
from config.paths_config import *
from utils.common_functions import read_yaml
from src.logger import get_logger
from src.custom_exception import CustomException

if __name__ == "__main__":
    logger = get_logger(__name__)
    try:
        logger.info("Starting the training pipeline...")

        # Data Processing Step
        processor = DataProcessor(input_file=ANIMELIST_CSV, output_dir=PROCESSED_DIR)
        processor.run_data_processing()

        # Model Training Step
        model_trainer = ModelTraining(data_path=PROCESSED_DIR)
        model_trainer.train_model()

        logger.info("Training pipeline executed successfully.")

    except Exception as e:
        logger.error("Error in the training pipeline: ", str(e))
        raise CustomException("Error in the training pipeline", e)