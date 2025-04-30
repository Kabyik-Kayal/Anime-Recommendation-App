import os

######################## Data Ingestion ########################
# Define base directory
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config/config.yaml")

######################### Data Processing ########################
# Define data directories
RAW_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

# Define data file paths
ANIMELIST_CSV = os.path.join(RAW_DIR, "animelist.csv")
ANIME_CSV = os.path.join(RAW_DIR, "anime.csv")
SYNOPSIS_CSV = os.path.join(RAW_DIR, "anime_with_synopsis.csv")

# Define processed data file paths
PROCESSED_ANIME_DF = os.path.join(PROCESSED_DIR, "anime_df.csv")
PROCESSED_RATING_DF = os.path.join(PROCESSED_DIR, "rating_df.csv")
PROCESSED_SYNOPSIS_DF = os.path.join(PROCESSED_DIR, "synopsis_df.csv")

X_TEST_ARRAY_PATH = os.path.join(PROCESSED_DIR, "X_test_array.pkl")
X_TRAIN_ARRAY_PATH = os.path.join(PROCESSED_DIR, "X_train_array.pkl")
Y_TEST_PATH = os.path.join(PROCESSED_DIR, "y_test.pkl")
Y_TRAIN_PATH = os.path.join(PROCESSED_DIR, "y_train.pkl")

# Define encoded and decoded data file paths
ANIME2ANIME_ENCODED_PATH = os.path.join(PROCESSED_DIR, "anime2anime_encoded.pkl")
ANIME2ANIME_DECODED_PATH = os.path.join(PROCESSED_DIR, "anime2anime_decoded.pkl")
USER2USER_ENCODED_PATH = os.path.join(PROCESSED_DIR, "user2user_encoded.pkl")
USER2USER_DECODED_PATH = os.path.join(PROCESSED_DIR, "user2user_decoded.pkl")

######################### Model Training ########################
# Define model directories
MODEL_DIR = os.path.join(BASE_DIR, "model")
WEIGHTS_DIR = os.path.join(MODEL_DIR, "weights")
MODEL_FILE_PATH = os.path.join(MODEL_DIR, "model.h5")
ANIME_WEIGHTS_FILE_PATH = os.path.join(WEIGHTS_DIR, "anime_weights.pkl")
USER_WEIGHTS_FILE_PATH = os.path.join(WEIGHTS_DIR, "user_weights.pkl")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "model_checkpoints")
CHECKPOINT_FILE_PATH = os.path.join(CHECKPOINT_DIR, "checkpoint.weights.h5")