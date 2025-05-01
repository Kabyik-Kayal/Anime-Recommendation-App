import os # Import os module
import pandas as pd
import numpy as np
import joblib
import sys # Ensure sys is imported
from config.paths_config import *
from src.logger import get_logger
from src.custom_exception import CustomException

# Ensure logger is initialized at the top
logger = get_logger(__name__)

# Load data and artifacts once when the module is imported
try:
    # Check if paths are valid before loading
    required_paths = {
        "PROCESSED_SYNOPSIS_DF": PROCESSED_SYNOPSIS_DF,
        "ANIME_WEIGHTS_FILE_PATH": ANIME_WEIGHTS_FILE_PATH,
        "USER_WEIGHTS_FILE_PATH": USER_WEIGHTS_FILE_PATH,
        "ANIME2ANIME_ENCODED_PATH": ANIME2ANIME_ENCODED_PATH,
        "ANIME2ANIME_DECODED_PATH": ANIME2ANIME_DECODED_PATH,
        "USER2USER_ENCODED_PATH": USER2USER_ENCODED_PATH,
        "USER2USER_DECODED_PATH": USER2USER_DECODED_PATH
    }
    for name, path in required_paths.items():
        if not os.path.exists(path):
             logger.error(f"Artifact file not found: {name} at {path}. Ensure training pipeline ran successfully.")
             raise FileNotFoundError(f"Missing artifact: {name} at {path}")

    synopsis_df = pd.read_csv(PROCESSED_SYNOPSIS_DF)
    anime_weights = joblib.load(ANIME_WEIGHTS_FILE_PATH)
    user_weights = joblib.load(USER_WEIGHTS_FILE_PATH)
    anime2anime_encoded = joblib.load(ANIME2ANIME_ENCODED_PATH)
    anime2anime_decoded = joblib.load(ANIME2ANIME_DECODED_PATH)
    user2user_encoded = joblib.load(USER2USER_ENCODED_PATH)
    user2user_decoded = joblib.load(USER2USER_DECODED_PATH)
    logger.info("All artifacts loaded successfully.")

except FileNotFoundError as e:
    logger.error(f"Error loading artifacts: {e}. Ensure training pipeline ran successfully and paths in config are correct.", exc_info=True)
    synopsis_df, anime_weights, user_weights, anime2anime_encoded, anime2anime_decoded, user2user_encoded, user2user_decoded = [None] * 7

except Exception as e:
    logger.error(f"Unexpected error loading artifacts: {e}", exc_info=True)
    synopsis_df, anime_weights, user_weights, anime2anime_encoded, anime2anime_decoded, user2user_encoded, user2user_decoded = [None] * 7
    raise CustomException(e, sys)

def getAnimeFrame(user_input, df):
    """Fetches the anime details row from the dataframe based on ID or name."""
    if df is None:
        logger.warning("getAnimeFrame called with df=None")
        return pd.DataFrame()
    try:
        if isinstance(user_input, (int, np.integer)):
            return df[df["anime_id"] == user_input]
        elif isinstance(user_input, str):
            return df[df["eng_version"].str.lower() == user_input.lower()]
        else:
            logger.warning(f"Invalid user_input type for getAnimeFrame: {type(user_input)}")
            return pd.DataFrame()
    except KeyError as e:
        logger.error(f"KeyError in getAnimeFrame: {e}. Check DataFrame columns.", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error in getAnimeFrame for input '{user_input}': {e}", exc_info=True)
        return pd.DataFrame()

def getSynopsis(user_input, df):
    """Fetches the synopsis based on MAL_ID or Name."""
    if df is None:
        logger.warning("getSynopsis called with df=None")
        return "Synopsis not available."
    try:
        if isinstance(user_input, (int, np.integer)):
            result = df[df["MAL_ID"] == user_input]
            if not result.empty:
                return result.sypnopsis.values[0]
        elif isinstance(user_input, str):
            result = df[df["Name"].str.lower() == user_input.lower()]
            if not result.empty:
                return result.sypnopsis.values[0]
        logger.warning(f"Synopsis not found for input: {user_input}")
        return "Synopsis not available."
    except KeyError as e:
        logger.error(f"KeyError in getSynopsis: {e}. Check DataFrame columns.", exc_info=True)
        return "Synopsis retrieval error."
    except Exception as e:
        logger.error(f"Error in getSynopsis for input '{user_input}': {e}", exc_info=True)
        return "Synopsis retrieval error."

def find_similar_anime(name, anime_df, synopsis_df, n=5, return_dist=False, neg=False):
    """Finds similar animes based on embedding weights."""
    if anime_weights is None or anime2anime_encoded is None or anime2anime_decoded is None:
        logger.error("Cannot find similar anime: Artifacts not loaded.")
        return pd.DataFrame(columns=["name", "similarity", "genre", "synopsis"])

    try:
        anime_frame_initial = getAnimeFrame(name, anime_df)
        if anime_frame_initial.empty:
            logger.warning(f"Could not find anime frame for input name/ID: {name}")
            return pd.DataFrame(columns=["name", "similarity", "genre", "synopsis"])

        index = anime_frame_initial.anime_id.values[0]
        encoded_index = anime2anime_encoded.get(index)

        if encoded_index is None:
            logger.warning(f"Anime ID {index} (from name '{name}') not found in anime2anime_encoded map.")
            return pd.DataFrame(columns=["name", "similarity", "genre", "synopsis"])

        weights = anime_weights
        if not isinstance(encoded_index, (int, np.integer)) or encoded_index < 0 or encoded_index >= len(weights):
            logger.warning(f"Encoded index {encoded_index} is invalid or out of bounds for weights array (length {len(weights)}). Name: '{name}', ID: {index}")
            return pd.DataFrame(columns=["name", "similarity", "genre", "synopsis"])

        dists = np.dot(weights, weights[encoded_index])
        sorted_dists_indices = np.argsort(dists)

        num_results = n + 1

        if neg:
            closest_indices = sorted_dists_indices[:num_results]
        else:
            closest_indices = sorted_dists_indices[-num_results:]

        logger.info(f"Finding {n} anime closest to '{name}' (ID: {index})")

        if return_dist:
            return dists, closest_indices

        SimilarityArray = []
        processed_decoded_ids = set()

        # Iterate through the indices of closest animes
        for close_idx in reversed(closest_indices): # Process from most similar down
            if len(SimilarityArray) >= n:
                 break # Stop once we have enough valid recommendations

            decoded_id = anime2anime_decoded.get(close_idx)

            # --- Start: Checks for each potential recommendation --- 
            if decoded_id is None:
                logger.warning(f"Decoded ID is None for similarity index {close_idx}")
                continue

            # Avoid duplicates if multiple indices map to the same ID (shouldn't happen with good encoding)
            if decoded_id in processed_decoded_ids:
                continue

            # Exclude the input anime itself
            if decoded_id == index:
                continue

            # Check if the anime exists in the main anime dataframe
            anime_frame = getAnimeFrame(decoded_id, anime_df)
            if anime_frame.empty:
                logger.warning(f"Similar anime (Decoded ID: {decoded_id}, Index: {close_idx}) not found in anime_df.")
                continue

            # Check if the anime exists in the synopsis dataframe
            if synopsis_df is None or decoded_id not in synopsis_df['MAL_ID'].values:
                 logger.warning(f"Synopsis info missing for similar anime (Decoded ID: {decoded_id}, Index: {close_idx}). MAL_ID lookup failed.")
                 synopsis = "Synopsis not available."
                 # continue # Uncomment this to skip if synopsis is mandatory
            else:
                 synopsis = getSynopsis(decoded_id, synopsis_df)
            # --- End: Checks --- 

            try:
                anime_name = anime_frame["eng_version"].values[0]
                genre = anime_frame["Genres"].values[0]
                # Ensure index is valid before accessing distance
                if close_idx < 0 or close_idx >= len(dists):
                     logger.warning(f"Similarity index {close_idx} out of bounds for dists array.")
                     continue
                similarity = dists[close_idx]

                SimilarityArray.append({
                    "name": anime_name,
                    "similarity": similarity,
                    "genre": genre,
                    "synopsis": synopsis
                })
                processed_decoded_ids.add(decoded_id)

            except KeyError as e:
                 logger.error(f"KeyError accessing data for similar anime '{anime_name}' (Decoded ID: {decoded_id}): {e}", exc_info=True)
                 continue # Skip this problematic anime
            except IndexError as e:
                 logger.error(f"IndexError accessing data for similar anime (Decoded ID: {decoded_id}, Index: {close_idx}): {e}", exc_info=True)
                 continue # Skip this problematic anime
            except Exception as e:
                logger.error(f"Unexpected error processing similar anime candidate {close_idx} (Decoded ID: {decoded_id}): {e}", exc_info=True)
                continue # Skip this problematic anime

        if not SimilarityArray:
             logger.warning(f"No valid similar anime found for '{name}' after processing candidates.")
             return pd.DataFrame(columns=["name", "similarity", "genre", "synopsis"])

        # Create DataFrame from the collected valid recommendations
        Frame = pd.DataFrame(SimilarityArray)
    
        return Frame.head(n) # Return top N valid results

    except KeyError as e:
         logger.error(f"KeyError during initial lookup for '{name}': {e}. Check anime_df columns.", exc_info=True)
         return pd.DataFrame(columns=["name", "similarity", "genre", "synopsis"])
    except IndexError as e:
         logger.error(f"IndexError during initial lookup or weight access for '{name}'. Is encoded_index {encoded_index} valid? Error: {e}", exc_info=True)
         return pd.DataFrame(columns=["name", "similarity", "genre", "synopsis"])
    except Exception as e:
        logger.error(f"General Error in find_similar_anime for '{name}': {e}", exc_info=True)
        return pd.DataFrame(columns=["name", "similarity", "genre", "synopsis"])

def find_similar_user(user_id, n=5, return_dist=False, neg=False):
    """Finds similar users based on embedding weights."""
    if user_weights is None or user2user_encoded is None or user2user_decoded is None:
        logger.error("Cannot find similar user: Artifacts not loaded.")
        return pd.DataFrame(columns=["similar_users", "similarity"])

    try:
        encoded_index = user2user_encoded.get(user_id)

        if encoded_index is None:
            logger.warning(f"User ID {user_id} not found in user2user_encoded map.")
            return pd.DataFrame(columns=["similar_users", "similarity"])

        weights = user_weights
        if not isinstance(encoded_index, (int, np.integer)) or encoded_index < 0 or encoded_index >= len(weights):
            logger.warning(f"Encoded index {encoded_index} is invalid or out of bounds for user weights array (length {len(weights)}). User ID: {user_id}")
            return pd.DataFrame(columns=["similar_users", "similarity"])

        dists = np.dot(weights, weights[encoded_index])
        sorted_dists_indices = np.argsort(dists)

        num_results = n + 1 # +1 to exclude the input user itself later

        if neg:
            closest_indices = sorted_dists_indices[:num_results]
        else:
            closest_indices = sorted_dists_indices[-num_results:]

        logger.info(f"Finding {n} users closest to User ID: {user_id}")

        if return_dist:
            return dists, closest_indices

        SimilarityArray = []
        processed_decoded_ids = set()

        for close_idx in reversed(closest_indices): # Process from most similar down
            if len(SimilarityArray) >= n:
                break

            decoded_id = user2user_decoded.get(close_idx)

            if decoded_id is None:
                logger.warning(f"Decoded User ID is None for similarity index {close_idx}")
                continue

            if decoded_id in processed_decoded_ids:
                continue

            # Exclude the input user itself
            if decoded_id == user_id:
                continue

            try:
                 # Ensure index is valid before accessing distance
                if close_idx < 0 or close_idx >= len(dists):
                     logger.warning(f"User similarity index {close_idx} out of bounds for dists array.")
                     continue
                similarity = dists[close_idx]

                SimilarityArray.append({
                    "similar_users": decoded_id,
                    "similarity": similarity
                })
                processed_decoded_ids.add(decoded_id)

            except IndexError as e:
                 logger.error(f"IndexError accessing user similarity data (Decoded ID: {decoded_id}, Index: {close_idx}): {e}", exc_info=True)
                 continue
            except Exception as e:
                logger.error(f"Unexpected error processing similar user candidate {close_idx} (Decoded ID: {decoded_id}): {e}", exc_info=True)
                continue

        if not SimilarityArray:
            logger.warning(f"No valid similar users found for User ID {user_id} after processing candidates.")
            return pd.DataFrame(columns=["similar_users", "similarity"])

        similar_users_df = pd.DataFrame(SimilarityArray)
        return similar_users_df.head(n)

    except IndexError as e:
         logger.error(f"IndexError during user lookup or weight access for User ID {user_id}. Is encoded_index {encoded_index} valid? Error: {e}", exc_info=True)
         return pd.DataFrame(columns=["similar_users", "similarity"])
    except Exception as e:
        logger.error(f"General Error in find_similar_user for User ID {user_id}: {e}", exc_info=True)
        return pd.DataFrame(columns=["similar_users", "similarity"])

def get_user_preferences(user_id, ratings_df, anime_df, verbose=0):
    """Gets the preferred animes for a user based on their higher ratings."""
    if ratings_df is None or anime_df is None:
        logger.warning("get_user_preferences called with None DataFrame(s).")
        return pd.DataFrame(columns=["eng_version", "Genres"])

    try:
        animes_watched_by_user = ratings_df[ratings_df["user_id"] == user_id]
        if animes_watched_by_user.empty:
            logger.info(f"User {user_id} has no ratings data.")
            return pd.DataFrame(columns=["eng_version", "Genres"])

        # Use a threshold if percentile calculation fails (e.g., few ratings)
        try:
            # Ensure ratings are suitable for percentile (e.g., not all identical)
            if animes_watched_by_user["rating"].nunique() > 1:
                 user_rating_percentile = np.percentile(animes_watched_by_user["rating"], 75)
            else:
                 # Handle case with single unique rating or no ratings
                 user_rating_percentile = animes_watched_by_user["rating"].iloc[0] if not animes_watched_by_user.empty else 0
        except Exception as e:
            logger.warning(f"Could not calculate percentile for user {user_id}, using mean. Error: {e}")
            user_rating_percentile = animes_watched_by_user["rating"].mean()

        # Filter by percentile/threshold
        animes_watched_by_user = animes_watched_by_user[animes_watched_by_user["rating"] >= user_rating_percentile]
        if animes_watched_by_user.empty:
             logger.info(f"User {user_id} has no ratings at or above the 75th percentile ({user_rating_percentile:.2f}).")
             # Optionally, could return all watched animes or an empty frame
             return pd.DataFrame(columns=["eng_version", "Genres"])

        top_animes_ids = animes_watched_by_user.sort_values(by="rating", ascending=False).anime_id.values

        # Fetch details for these top animes
        anime_df_rows = anime_df[anime_df["anime_id"].isin(top_animes_ids)]
        # Select and return relevant columns
        anime_df_rows = anime_df_rows[["eng_version", "Genres"]].drop_duplicates()

        if verbose != 0:
            logger.info(f"User {user_id} preferences based on {len(anime_df_rows)} animes rated >= {user_rating_percentile:.2f}")
            # logger.info(f"Top 5 preferred animes for user {user_id}:\n{anime_df_rows.head(5)}") # Avoid printing large frames to log

        return anime_df_rows

    except KeyError as e:
        logger.error(f"KeyError in get_user_preferences for user {user_id}: {e}. Check DataFrame columns.", exc_info=True)
        return pd.DataFrame(columns=["eng_version", "Genres"])
    except Exception as e:
        logger.error(f"Error in get_user_preferences for user {user_id}: {e}", exc_info=True)
        return pd.DataFrame(columns=["eng_version", "Genres"])

def get_user_based_recommendations(similar_users_df, user_preferences_df, anime_df, ratings_df, synopsis_df, n=5):
    """Generates recommendations based on similar users' preferences."""
    if similar_users_df is None or similar_users_df.empty:
        logger.warning("Cannot generate user-based recommendations: No similar users provided.")
        return pd.DataFrame(columns=["name", "number_of_user_preferences", "genre", "synopsis"])

    if user_preferences_df is None: # Allow empty user_preferences_df
         logger.warning("User preferences DataFrame is None, proceeding without filtering watched items.")
         user_preferences_df = pd.DataFrame(columns=["eng_version"]) # Create empty frame to avoid errors

    recommended_animes = []
    anime_list = [] # Collect potential anime names from similar users

    try:
        for user_id in similar_users_df["similar_users"].values:
            # Get preferences of the similar user
            sim_user_prefs_df = get_user_preferences(int(user_id), ratings_df, anime_df)

            if not sim_user_prefs_df.empty:
                # Filter out animes the target user has already preferred/watched
                pref_list_unwatched = sim_user_prefs_df[
                    ~sim_user_prefs_df["eng_version"].isin(user_preferences_df["eng_version"].values)
                ]
                if not pref_list_unwatched.empty:
                    anime_list.extend(pref_list_unwatched["eng_version"].tolist())

        if not anime_list:
            logger.warning("No potential recommendations found from similar users' preferences.")
            return pd.DataFrame(columns=["name", "number_of_user_preferences", "genre", "synopsis"])

        # Count occurrences of each anime suggested by similar users
        anime_counts = pd.Series(anime_list).value_counts()
        sorted_list = anime_counts.head(n * 2) # Get more candidates initially

        logger.info(f"Found {len(anime_counts)} unique anime candidates from similar users.")

        processed_recommendations = []
        # Fetch details for the top candidates
        for anime_name, count in sorted_list.items():
            if len(processed_recommendations) >= n:
                break

            if isinstance(anime_name, str):
                try:
                    frame = getAnimeFrame(anime_name, anime_df)
                    if frame.empty:
                        logger.warning(f"Could not get frame for recommended anime: {anime_name}")
                        continue

                    anime_id = frame["anime_id"].values[0]
                    genre = frame["Genres"].values[0]
                    synopsis = getSynopsis(anime_id, synopsis_df) # Use ID for synopsis

                    processed_recommendations.append({
                        # "anime_id": anime_id, # Keep internally if needed
                        "name": anime_name,
                        "number_of_user_preferences": count,
                        "genre": genre,
                        "synopsis": synopsis
                    })
                except KeyError as e:
                    logger.error(f"KeyError processing user-based recommendation '{anime_name}': {e}", exc_info=True)
                    continue
                except IndexError as e:
                    logger.error(f"IndexError processing user-based recommendation '{anime_name}': {e}", exc_info=True)
                    continue
                except Exception as e:
                    logger.error(f"Error processing user-based recommendation '{anime_name}': {e}", exc_info=True)
                    continue
            else:
                 logger.warning(f"Skipping non-string anime name in recommendation list: {anime_name}")

        if not processed_recommendations:
             logger.warning("Could not fetch details for any top user-based candidates.")
             return pd.DataFrame(columns=["name", "number_of_user_preferences", "genre", "synopsis"])

        return pd.DataFrame(processed_recommendations).head(n)

    except KeyError as e:
        logger.error(f"KeyError in get_user_based_recommendations: {e}. Check DataFrame columns.", exc_info=True)
        return pd.DataFrame(columns=["name", "number_of_user_preferences", "genre", "synopsis"])
    except Exception as e:
        logger.error(f"General Error in get_user_based_recommendations: {e}", exc_info=True)
        return pd.DataFrame(columns=["name", "number_of_user_preferences", "genre", "synopsis"])

def get_content_based_recommendations_for_anime(anime_name, anime_df, synopsis_df, n=5):
    """Generates content-based recommendations for a given anime name."""
    logger.info(f"--- Starting Content-Based Recommendation for Anime: {anime_name} ---")
    try:
        similar_animes_df = find_similar_anime(anime_name, anime_df, synopsis_df, n=n)
        if similar_animes_df is None or similar_animes_df.empty:
            logger.warning(f"Could not find similar anime for '{anime_name}'.")
            return []

        recommendations = similar_animes_df["name"].tolist()
        logger.info(f"Found {len(recommendations)} content-based recommendations for '{anime_name}': {recommendations}")
        logger.info(f"--- Finished Content-Based Recommendation for Anime: {anime_name} ---")
        return recommendations
    except Exception as e:
        logger.error(f"Error in get_content_based_recommendations_for_anime for '{anime_name}': {e}", exc_info=True)
        return []


def hybrid_recommendation(user_id, ratings_df, anime_df, user_weight=0.5, content_weight=0.5, n=5):
    """Generates hybrid recommendations combining user-based and content-based approaches."""
    logger.info(f"--- Starting Hybrid Recommendation for User ID: {user_id} ---")

    # --- 1. User-Based Component --- 
    logger.info("Step 1: Finding similar users...")
    similar_users = find_similar_user(user_id, n=20) # Find more similar users initially
    if similar_users.empty:
        logger.warning(f"No similar users found for {user_id}. Cannot proceed with user-based part.")
        # Optionally: Fallback to pure content-based or return empty
        # For now, continue to content-based, but user-based score will be 0

    logger.info("Step 2: Getting target user preferences...")
    user_preferences = get_user_preferences(user_id, ratings_df, anime_df)

    logger.info("Step 3: Getting recommendations from similar users...")
    user_recommended_animes_df = get_user_based_recommendations(similar_users, user_preferences, anime_df, ratings_df, synopsis_df, n=n*2) # Get more candidates

    user_rec_list = []
    if not user_recommended_animes_df.empty:
        user_rec_list = user_recommended_animes_df["name"].tolist()
        logger.info(f"Found {len(user_rec_list)} initial user-based recommendations: {user_rec_list}")
    else:
        logger.warning("No recommendations generated from similar users.")

    # --- 2. Content-Based Component --- 
    logger.info("Step 4: Finding content-based recommendations based on user preferences...")
    content_recommended_anime_list = []
    # Use user's *own* preferences to find similar content
    if not user_preferences.empty:
        # Consider top N preferences for finding similar content
        top_pref_animes = user_preferences["eng_version"].head(n).tolist()
        logger.info(f"Finding content similar to top preferences: {top_pref_animes}")
        for anime_name_pref in top_pref_animes:
            try:
                # Find anime similar to this preferred anime
                similar_animes_df = find_similar_anime(anime_name_pref, anime_df, synopsis_df, n=n)
                if similar_animes_df is not None and not similar_animes_df.empty:
                    # Add names, ensuring they are not already in the user's preferences
                    new_recs = similar_animes_df[
                        ~similar_animes_df["name"].isin(user_preferences["eng_version"].values)
                    ]["name"].tolist()
                    content_recommended_anime_list.extend(new_recs)
                    logger.debug(f"Found {len(new_recs)} content-based recs similar to '{anime_name_pref}'")
                else:
                    logger.debug(f"No content-based similar animes found for preferred anime: '{anime_name_pref}'")
            except Exception as e:
                logger.error(f"Error getting content-based recs for preferred anime '{anime_name_pref}': {e}", exc_info=True)
                continue
        # De-duplicate content recommendations
        content_recommended_anime_list = list(pd.Series(content_recommended_anime_list).unique())
        logger.info(f"Found {len(content_recommended_anime_list)} unique content-based recommendations (based on user prefs): {content_recommended_anime_list[:10]}...")
    else:
        logger.warning(f"User {user_id} has no preferences, cannot generate content-based recommendations based on them.")

    # --- 3. Combine Scores --- 
    logger.info("Step 5: Combining user-based and content-based scores...")
    combined_scores = {}

    # Add scores from user-based recommendations
    # Use the count/rank from user_recommended_animes_df if available for weighting?
    # Simple approach: constant weight for being in the list
    for anime_name in user_rec_list:
        combined_scores[anime_name] = combined_scores.get(anime_name, 0) + user_weight

    # Add scores from content-based recommendations
    for anime_name in content_recommended_anime_list:
        # Avoid double-counting heavily if an item is in both lists
        # Option 1: Simple addition
        combined_scores[anime_name] = combined_scores.get(anime_name, 0) + content_weight
        # Option 2: Maximize score (if it appears in both, gets max weight)
        # combined_scores[anime_name] = max(combined_scores.get(anime_name, 0), content_weight)

    # Filter out animes already preferred by the user
    animes_to_exclude = set(user_preferences["eng_version"].values)
    final_scores = {anime: score for anime, score in combined_scores.items() if anime not in animes_to_exclude}

    if not final_scores:
        logger.warning(f"No combined recommendations generated for user {user_id} after filtering.")
        # Fallback? Recommend top popular animes?
        return []

    # Sort by combined score
    sorted_animes = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)

    logger.info(f"Generated {len(sorted_animes)} final combined recommendations.")
    logger.info(f"Top {n} recommendations for user {user_id}: {sorted_animes[:n]}")
    logger.info(f"--- Finished Hybrid Recommendation for User ID: {user_id} ---")

    # Return only the names of the top N animes
    return [anime_name for anime_name, score in sorted_animes[:n]]
