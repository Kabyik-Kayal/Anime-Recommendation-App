import os

######################## Data Ingestion ########################
# Define base directory
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")
CONFIG_PATH = os.path.join(BASE_DIR, "config")

######################### Data Processing ########################
# Define data directories
RAW_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

# Define data file paths
ANIMELIST_CSV = os.path.join(RAW_DIR, "animelist.csv")
ANIME_CSV = os.path.join(RAW_DIR, "anime.csv")
SYNOPSIS_CSV = os.path.join(RAW_DIR, "anime_with_synopsis.csv")