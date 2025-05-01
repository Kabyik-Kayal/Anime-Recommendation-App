from config.paths_config import *
from utils.helpers import *
from src.logger import get_logger
from src.custom_exception import CustomException
import pandas as pd

logger = get_logger(__name__)

# Load dataframes once
try:
    anime_df = pd.read_csv(PROCESSED_ANIME_DF)
    ratings_df = pd.read_csv(PROCESSED_RATING_DF)
    synopsis_df = pd.read_csv(PROCESSED_SYNOPSIS_DF) # Load synopsis_df needed for content-based
    logger.info("DataFrames loaded successfully for prediction pipeline.")
except FileNotFoundError as e:
    logger.error(f"Error loading dataframes in prediction pipeline: {e}. Ensure paths are correct and data exists.", exc_info=True)
    # Handle error appropriately, maybe exit or use placeholder data if applicable
    anime_df, ratings_df, synopsis_df = None, None, None
except Exception as e:
    logger.error(f"Unexpected error loading dataframes: {e}", exc_info=True)
    anime_df, ratings_df, synopsis_df = None, None, None
    # Consider raising the exception or handling it based on application needs


def predict_anime_hybrid(userID):
    """Predicts anime using the hybrid recommendation system for a user ID."""
    if anime_df is None or ratings_df is None:
         logger.error("Cannot run hybrid prediction: DataFrames not loaded.")
         return []
    try:
        recommendation = hybrid_recommendation(user_id=userID, ratings_df=ratings_df, anime_df=anime_df, user_weight=0.5, content_weight=0.5)
        return recommendation
    except Exception as e:
        logger.error(f"Error during hybrid prediction for user {userID}: {e}", exc_info=True)
        raise CustomException(e, sys) # Re-raise as CustomException


def predict_similar_anime(anime_name):
    """Predicts similar anime based on content for a given anime name."""
    if anime_df is None or synopsis_df is None:
        logger.error("Cannot run content-based prediction: DataFrames not loaded.")
        return []
    try:
        # Use the new helper function
        recommendations = get_content_based_recommendations_for_anime(anime_name=anime_name, anime_df=anime_df, synopsis_df=synopsis_df, n=5)
        return recommendations
    except Exception as e:
        logger.error(f"Error during content-based prediction for anime '{anime_name}': {e}", exc_info=True)
        raise CustomException(e, sys) # Re-raise as CustomException


def get_all_user_ids():
    """Returns a list of all unique user IDs from the ratings dataframe."""
    if ratings_df is None:
        logger.error("Cannot get user IDs: ratings_df not loaded.")
        return []
    try:
        unique_ids = sorted(ratings_df['user_id'].unique().tolist())
        logger.info(f"Retrieved {len(unique_ids)} unique user IDs.")
        return unique_ids
    except KeyError:
        logger.error("'user_id' column not found in ratings_df.")
        return []
    except Exception as e:
        logger.error(f"Error retrieving user IDs: {e}", exc_info=True)
        return []

if __name__ == "__main__":
    # Test hybrid prediction
    userID = 1980
    try:
        hybrid_recs = predict_anime_hybrid(userID)
        print(f"Hybrid Recommendations for user {userID}: {hybrid_recs}")
    except Exception as e:
        print(f"Error testing hybrid prediction: {e}")

    # Test content-based prediction
    anime_name_test = "Naruto" # Example anime name
    try:
        content_recs = predict_similar_anime(anime_name_test)
        print(f"Content-Based Recommendations similar to '{anime_name_test}': {content_recs}")
    except Exception as e:
        print(f"Error testing content-based prediction: {e}")