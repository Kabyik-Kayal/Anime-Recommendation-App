from flask import Flask, render_template, request, jsonify # Import jsonify
# Import prediction functions and the new user ID getter
from pipeline.prediction_pipeline import predict_anime_hybrid, predict_similar_anime, get_all_user_ids
import sys
from src.custom_exception import CustomException
from src.logger import get_logger

app = Flask(__name__)
logger = get_logger(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        recommendations = None
        result_title = ""
        error_message = None # Variable for potential errors
        try:
            recommendation_type = request.form.get("recommendation_type")

            if recommendation_type == "user_id":
                user_id_str = request.form.get("UserID")
                if user_id_str: # Check if UserID was provided
                    user_id = int(user_id_str)
                    logger.info(f"Received request for hybrid recommendation for User ID: {user_id}")
                    recommendations = predict_anime_hybrid(user_id)
                    # Change the result title here
                    result_title = "Anime Recommendations from User" 
                else:
                     logger.warning("User ID form submitted but UserID field was empty.")
                     error_message = "Please select a User ID."

            elif recommendation_type == "anime_name":
                anime_name = request.form.get("AnimeName")
                if anime_name: # Check if AnimeName was provided
                    logger.info(f"Received request for content-based recommendation for Anime: {anime_name}")
                    recommendations = predict_similar_anime(anime_name)
                    result_title = f"Anime Similar to '{anime_name}'"
                else:
                    logger.warning("Anime Name form submitted but AnimeName field was empty.")
                    error_message = "Please enter an Anime Name."
            else:
                logger.warning(f"Received POST request with unknown recommendation_type: {recommendation_type}")
                error_message = "Invalid request type."

        except ValueError:
             logger.error(f"Invalid input received. Could not convert User ID to integer.", exc_info=True)
             error_message = "Invalid User ID provided."
             recommendations = [] # Ensure recommendations is an empty list on error
        except CustomException as e:
            logger.error(f"CustomException occurred during prediction: {e}", exc_info=True)
            error_message = "An error occurred while generating recommendations."
            recommendations = []
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            error_message = "An unexpected server error occurred."
            recommendations = [] # Ensure recommendations is an empty list on error

        # Return JSON response for POST requests
        return jsonify({
            'recommendations': recommendations,
            'result_title': result_title,
            'error': error_message
        })

    # Handle GET request: Render the initial page
    user_ids = get_all_user_ids()
    return render_template('index.html', user_ids=user_ids)


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=5000)