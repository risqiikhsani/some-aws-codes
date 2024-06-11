import json
import uuid
import boto3
from botocore.exceptions import ClientError
import logging
import base64
import os

client = boto3.client('rekognition')
logger = logging.getLogger()
logger.setLevel("INFO")
BUCKET="myapp-images-bucket"
PROJECT_ARN = os.environ.get("PROJECT_ARN")
VERSION_NAME = os.environ.get("VERSION_NAME")
MODEL = os.environ.get("MODEL")
MIN_CONFIDENCE=50

def response_payload(err, res=None):
    if err:
        error_message = str(err)
        status_code = 502
        response_body = {"error": {"message": error_message}}
    else:
        status_code = 200
        response_body = res

    return {
        "statusCode": status_code,
        "body": json.dumps(response_body),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
    }

def show_custom_labels(model,bucket,photo, min_confidence):
    client=boto3.client('rekognition')

    try:
        #Call DetectCustomLabels
        response = client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
            MinConfidence=min_confidence,
            ProjectVersionArn=model)
        return response_payload(None, {"response": response["CustomLabels"]})
    except Exception as e:
        logger.error(e)
        return response_payload(e)
        
    logger.info("done check model")

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    user = "test"
    if "authorizer" in event["requestContext"]:
        user = event["requestContext"]["authorizer"]["claims"]["sub"]
        
    http_method = event['httpMethod']
    if http_method == 'GET':
        
        query_string_parameters = event.get('queryStringParameters', {})

        # Check if query_string_parameters is None
        if query_string_parameters is None:
            query_string_parameters = {}
    
        photo = query_string_parameters.get('image_key', None)
    
        # Ensure at least one of post_id or comment_id is provided
        if not photo:
            error_message = "photo must be provided"
            logger.error(error_message)
            return response_payload(error_message, None)
            
        return show_custom_labels(MODEL,BUCKET,photo,MIN_CONFIDENCE)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return response_payload("Method Not Allowed")

