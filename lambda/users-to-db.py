import json
import uuid
import boto3
from botocore.exceptions import ClientError
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel("INFO")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

def lambda_handler(event, context):
    print(event)
    user_sub = event['request']['userAttributes']['sub']
    user_email = event['request']['userAttributes']['email']
    name = user_email.split("@")[0]
    try:
        table.put_item(Item={
        'id': user_sub, 
        'name': name,
        })
        logger.info(f"User created successfully with ID: {user_sub}")
    except Exception as e:
        logger.error(f"Error creating user: {e}")

    

    # Return to Amazon Cognito
    return event