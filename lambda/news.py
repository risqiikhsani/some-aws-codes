import os
import requests
import logging
import json

# Initialize the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def get_news(event):
    """
    Fetches the top health headlines from the NewsAPI and returns the results.
    """

    # Get the NewsAPI key from an environment variable
    news_api_key = os.getenv("NEWS_API_KEY")
    if not news_api_key:
        logger.error("NewsAPI key not found in environment variables.")
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "NewsAPI key not found in environment variables."})
        }
    
    country = "us"
    # Uncomment this if you want to support country parameter from query string
    if "queryStringParameters" in event and "country" in event["queryStringParameters"]:
        country = event["queryStringParameters"]["country"]

    # Set the API endpoint and parameters
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": news_api_key,
        "country": country,
        "category": "health"
    }

    # Make the API request
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return {
            "statusCode": 200,
            "body": json.dumps(data)
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unexpected error: {str(e)}"})
        }

def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))
    
    try:
        http_method = event["httpMethod"]
        if http_method == "GET":
            return get_news(event)
        else:
            logger.error(f"Unsupported HTTP method: {http_method}")
            return {
                "statusCode": 405,
                "body": json.dumps({"error": "Unsupported HTTP method"})
            }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unexpected error: {e}"})
        }

# Example event for testing locally
if __name__ == "__main__":
    event = {
        "httpMethod": "GET",
        "queryStringParameters": {}
    }
    context = {}
    print(lambda_handler(event, context))
