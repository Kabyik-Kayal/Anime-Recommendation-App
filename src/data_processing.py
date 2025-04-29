import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *
from config.paths_config import ANIMELIST_CSV
import sys

logger = get_logger(__name__)

class DataProcessor:
    def __init__(self, input_file:str , output_dir:str):
        self.input_file = input_file
        self.output_dir = output_dir

        self.rating_df = None
        self.anime_df = None
        self.X_train_array = None
        self.X_test_array = None
        self.y_train = None
        self.y_test = None

        self.user2user_encoded = {}
        self.user2user_decoded = {}
        self.anime2anime_encoded = {}
        self.anime2anime_decoded = {}

        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("Data Processor initialized.")

    def load_data(self):
        try:
            self.rating_df = pd.read_csv(self.input_file, low_memory=True, usecols=["user_id", "anime_id", "rating"])
            logger.info(f"Data loaded from {self.input_file}.")
        except Exception as e:
            raise CustomException(f"Failed to load data from {self.input_file}, {e}",sys)
        
    def filter_users(self, min_rating = 50):
        try:
            n_ratings = self.rating_df['user_id'].value_counts()
            self.rating_df = self.rating_df[self.rating_df['user_id'].isin(n_ratings[n_ratings >= min_rating].index)]
            logger.info(f"Filtered users with those who have rated more than {min_rating} animes.")
        except Exception as e:
            raise CustomException(f"Failed to filter users, {e}",sys)
    
    def scale_rating(self):
        min_rating = min(self.rating_df['rating'])
        max_rating = max(self.rating_df['rating'])
        try:
            self.rating_df['rating'] = self.rating_df["rating"].apply(lambda x: (x - min_rating)/(max_rating - min_rating)).values.astype(np.float64)
            logger.info("Ratings scaled to [0, 1].")
        except Exception as e:
            raise CustomException(f"Failed to scale ratings, {e}",sys)
    
    def encode_data(self):
        try:
            self.user2user_encoded = {x: i for i, x in enumerate(self.rating_df['user_id'].unique())}
            self.user2user_decoded = {i: x for i, x in enumerate(self.rating_df['user_id'].unique())}
            self.rating_df['user'] = self.rating_df['user_id'].map(self.user2user_encoded)
            self.anime2anime_encoded = {x: i for i, x in enumerate(self.rating_df['anime_id'].unique())}
            self.anime2anime_decoded = {i: x for i, x in enumerate(self.rating_df['anime_id'].unique())}
            self.rating_df['anime'] = self.rating_df['anime_id'].map(self.anime2anime_encoded)
            logger.info("Data encoded successfully for User Id and Anime ID.")
        except Exception as e:
            raise CustomException(f"Failed to encode data, {e}",sys)
    
    def split_data(self, test_size=1000, random_state=42):
        try:
            self.rating_df = self.rating_df.sample(frac = 1, random_state=random_state).reset_index(drop=True)
            X = self.rating_df[["user", "anime"]].values
            y = self.rating_df["rating"]
            train_indices = self.rating_df.shape[0] - test_size
            X_train, X_test, y_train, y_test = (
                                                X[:train_indices],
                                                X[train_indices:],
                                                y[:train_indices],
                                                y[train_indices:]
                                                )
            self.X_train_array = [ X_train[:,0], X_train[:,1]]
            self.X_test_array = [ X_test[:,0], X_test[:,1]]

            self.y_train = y_train
            self.y_test = y_test

            logger.info(f"Data splitted successfully into train and test sets with test size {test_size}.")
        except Exception as e:
            raise CustomException(f"Failed to split data, {e}",sys)
    
    def save_artifacts(self):
        try:
            artifacts = {
                "user2user_encoded": self.user2user_encoded,
                "user2user_decoded": self.user2user_decoded,
                "anime2anime_encoded": self.anime2anime_encoded,
                "anime2anime_decoded": self.anime2anime_decoded,
                "X_train_array": self.X_train_array,
                "X_test_array": self.X_test_array,
                "y_train": self.y_train,
                "y_test": self.y_test
            }

            for name,data in artifacts.items():
                try:
                    joblib.dump(data, os.path.join(self.output_dir,f"{name}.pkl"))
                    logger.info(f"Artifact {name} saved successfully.")
                except Exception as e:
                    raise CustomException(f"Failed to save artifact {name}, {e}",sys)
            
            self.rating_df.to_csv(os.path.join(self.output_dir,"rating_df.csv"), index=False)
            logger.info("rating_df saved successfully.")

        except Exception as e:
            raise CustomException(f"Failed to save artifacts, {e}",sys)
        
    def get_anime_name(self, df:pd.DataFrame, anime_id):
        try:
            name = df[df.anime_id == anime_id].eng_version.values[0]
            if name is np.nan:
                name = df[df.anime_id == anime_id].Name.values[0]
        except:
            print(f"Anime id {anime_id} not found")
        return name

    def process_anime_data(self):
        try:
            anime_df = pd.read_csv(ANIME_CSV)
            anime_df = anime_df.replace("Unknown", np.nan)

            synopsis_cols = ["MAL_ID","Name","Genres","sypnopsis"]
            synopsis_df = pd.read_csv(SYNOPSIS_CSV, usecols=synopsis_cols)
            
            anime_df["anime_id"] = anime_df["MAL_ID"]
            anime_df["eng_version"] = anime_df["English name"]
            anime_df["eng_version"] = anime_df.anime_id.apply(lambda x: self.get_anime_name(anime_df, x))
            anime_df.sort_values(by=["Score"], inplace=True, ascending=False, kind="quicksort", na_position="last")

            anime_df = anime_df[["anime_id", "eng_version", "Score", "Genres", "Episodes", "Type", "Premiered", "Members"]]
            
            anime_df.to_csv(os.path.join(self.output_dir,"anime_df.csv"), index=False)
            synopsis_df.to_csv(os.path.join(self.output_dir,"synopsis_df.csv"), index=False)

        except Exception as e:
            raise CustomException(f"Failed to save processed anime data, {e}",sys)
    
    def run_data_processing(self):
        try:
            self.load_data()
            self.filter_users()
            self.scale_rating()
            self.encode_data()
            self.split_data()
            self.save_artifacts()
            self.process_anime_data()
            logger.info("Data processing completed successfully.")
        except Exception as e:
            raise CustomException(f"Failed to run data processing, {e}",sys)

if __name__ == "__main__":
    processor = DataProcessor(input_file=ANIMELIST_CSV, output_dir=PROCESSED_DIR)
    processor.run_data_processing()