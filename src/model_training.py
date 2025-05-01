import os
import comet_ml
import numpy as np
import joblib
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, LearningRateScheduler, TensorBoard
from src.logger import get_logger
from src.custom_exception import CustomException
from src.base_model import BaseModel
from config.paths_config import *
from dotenv import load_dotenv

logger = get_logger(__name__)

class ModelTraining:
    def __init__(self, data_path):
        try:
            self.data_path = data_path
            logger.info("Model initialized successfully.")

            load_dotenv()
            self.experiment = comet_ml.Experiment(
                api_key=os.getenv("COMET_ML_API_KEY"),
                project_name=os.getenv("COMET_ML_PROJECT_NAME"),
                workspace=os.getenv("COMET_ML_WORKSPACE")
                )
            logger.info("Comet ML experiment initialized successfully.")

        except Exception as e:
            logger.error("Error initializing model: %s", str(e))
            raise CustomException("Error initializing model", e)
    
    def load_data(self):
        try:
            X_train_array = joblib.load(X_TRAIN_ARRAY_PATH)
            X_test_array = joblib.load(X_TEST_ARRAY_PATH)
            y_train = joblib.load(Y_TRAIN_PATH)
            y_test = joblib.load(Y_TEST_PATH)

            logger.info("Data loaded successfully.")
            return X_train_array, X_test_array, y_train, y_test
        
        except Exception as e:
            logger.error("Error loading data: %s", str(e))
            raise CustomException("Error loading data", e)
        
    def train_model(self):
        try:
            X_train_array, X_test_array, y_train, y_test = self.load_data()
            
            n_users = len(joblib.load(USER2USER_ENCODED_PATH))
            n_anime = len(joblib.load(ANIME2ANIME_ENCODED_PATH))

            base_model = BaseModel(config_path=CONFIG_PATH)

            model = base_model.RecommenderNet(n_users, n_anime)

            start_lr = 0.00001
            min_lr = 0.0001
            max_lr = 0.00005
            batch_size = 10000

            ramup_epochs = 5
            sustain_epochs = 0
            exp_decay = 0.8

            os.makedirs(CHECKPOINT_DIR, exist_ok=True)
            os.makedirs(WEIGHTS_DIR, exist_ok=True)
            os.makedirs(MODEL_DIR, exist_ok=True)

            def lrfn(epoch):
                if epoch < ramup_epochs:
                    return (max_lr-start_lr)/ramup_epochs*epoch + start_lr
                elif epoch < ramup_epochs+sustain_epochs:
                    return max_lr
                else:
                    return(max_lr-min_lr)*exp_decay**(epoch-ramup_epochs-sustain_epochs)+min_lr
                
            lr_callback = LearningRateScheduler(lambda epoch:lrfn(epoch), verbose = 0)
            model_checkpoint = ModelCheckpoint(filepath=CHECKPOINT_FILE_PATH, save_weights_only=True, monitor='val_loss', mode='min', save_best_only=True)
            early_stopping = EarlyStopping(patience=5, monitor="val_loss", mode="min", restore_best_weights=True)
            my_callbacks = [model_checkpoint, lr_callback, early_stopping]

            try:
                history = model.fit(
                                    x = X_train_array,
                                    y = y_train,
                                    batch_size = batch_size,
                                    epochs = 20,
                                    verbose = 1,
                                    validation_data = (X_test_array, y_test),
                                    callbacks = my_callbacks
                                )
                model.load_weights(CHECKPOINT_FILE_PATH)
                logger.info("Model trained successfully.")

                for epoch in range(len(history.history['loss'])):
                    train_loss = history.history['loss'][epoch]
                    val_loss = history.history['val_loss'][epoch]

                    self.experiment.log_metric("train_loss", train_loss, step=epoch)
                    self.experiment.log_metric("val_loss", val_loss, step=epoch)

            except Exception as e:
                logger.error("Error during model training: %s", str(e))
                raise CustomException("Error during model training", e)

            self.save_model_weights(model)
            
        except Exception as e:
            logger.error("Error in train_model: %s", str(e))
            raise CustomException("Error in train_model", e)
    
    def extract_weights(self, name, model):
        try:
            weight_layer = model.get_layer(name)
            weights = weight_layer.get_weights()[0]
            weights = weights/np.linalg.norm(weights, axis=1).reshape((-1,1))
            logger.info("Weights extracted successfully.")
            return weights
        except Exception as e:
            logger.error("Error extracting weights: %s", str(e))
            raise CustomException("Error extracting weights", e)

    def save_model_weights(self, model):
        try:
            model.save(MODEL_FILE_PATH)
            logger.info("Model saved successfully.")

            user_weights = self.extract_weights("user_embedding", model)
            anime_weights = self.extract_weights("anime_embedding", model)

            joblib.dump(user_weights, USER_WEIGHTS_FILE_PATH)
            joblib.dump(anime_weights, ANIME_WEIGHTS_FILE_PATH)

            self.experiment.log_asset(MODEL_FILE_PATH)
            self.experiment.log_asset(USER_WEIGHTS_FILE_PATH)
            self.experiment.log_asset(ANIME_WEIGHTS_FILE_PATH)

            logger.info("User and Anime weights saved successfully.")
        except Exception as e:
            logger.error("Error saving model weights: %s", str(e))
            raise CustomException("Error saving model weights", e)
        
if __name__ == "__main__":
    model_trainer = ModelTraining(data_path=PROCESSED_DIR)
    model_trainer.train_model()