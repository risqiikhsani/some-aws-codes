import os
import requests

def lambda_handler(event, context):
    """
    Fetches the top health headlines from the NewsAPI and returns the results.
    """
    # Get the NewsAPI key from an environment variable
    news_api_key = os.getenv("NEWS_API_KEY")
    if not news_api_key:
        return {
            "statusCode": 500,
            "body": "NewsAPI key not found in environment variables."
        }

    # Set the API endpoint and parameters
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": news_api_key,
        "country": "us",
        "category": "health"
    }

    # Make the API request
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return {
            "statusCode": 500,
            "body": f"Error fetching news: {str(e)}"
        }

    # Return the response
    return {
        "statusCode": 200,
        "body": str(data)
    }
