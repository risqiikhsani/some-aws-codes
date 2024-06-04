import json
import uuid
import boto3
from botocore.exceptions import ClientError
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel("INFO")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('likes')

def check_authorization(like_id, user):
    logger.info("Checking user authorization")
    try:
        # Retrieve the like to check ownership
        response = table.get_item(Key={'id': like_id})
        if 'Item' not in response:
            logger.info(f"like not found with ID: {like_id}")
            return False, 'like not found'

        like = response['Item']
        if like['user'] != user:
            logger.warning(f"User {user} is not authorized to modify like with ID: {like_id}")
            return False, 'Unauthorized'
        
        return True, None
    except ClientError as e:
        logger.error(f"Error checking authorization: {e}")
        return False, f'Error checking authorization: {e}'
        
    logger.info("Done checking user authorization")
        
def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    http_method = event['httpMethod']
    if http_method == 'GET':
        if event["path"] == "/add":
            return create_like(event)
        elif event["path"] == "/remove":
            return delete_like(event)
        elif event["path"] == "/mine":
            return list_likes(event)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return response_payload("Method Not Allowed", None)
        
def list_likes(event):
    logger.info("Listing all user likes")
    user = event["requestContext"]["authorizer"]["claims"]["sub"] | None
    
    try:
        response = table.scan(
            FilterExpression=Attr('user').eq(user)
        )
        logger.info(f"Found {len(response['Items'])} likes for user {user}")
        return response_payload(None, response['Items'])
    except ClientError as e:
        logger.error(f"Error listing likes for user {user}: {e}")
        return response_payload(f'Error listing likes for user {user}: {e}', None)



def create_like(event):
    logger.info("Creating like")
    # Extract post_id from query parameters

    # Extract post_id and like_id from query parameters
    post_id = event['queryStringParameters'].get('post_id', '')
    like_id = event['queryStringParameters'].get('like_id', '')

    # Ensure at least one of post_id or like_id is provided
    if not post_id and not like_id:
        error_message = "Either post_id or like_id must be provided"
        logger.error(error_message)
        return response_payload(error_message, None)

    like_id = str(uuid.uuid4())
    time_creation = datetime.utcnow().isoformat()
    user = event["requestContext"]["authorizer"]["claims"]["sub"] | None
    
    try:
        table.put_item(Item={
        'id': like_id, 
        'post_id':post_id,
        'like_id':like_id,
        'time_creation': time_creation,
        'user': user, })
        logger.info(f"like created successfully with ID: {like_id}")
        return response_payload(None, 'like created successfully')
    except Exception as e:
        logger.error(f"Error creating like: {e}")
        return response_payload(f'Error creating like: {e}', None)
    logger.info("Done Creating a new like")


    
def delete_like(event):
    logger.info("Delete like")
    # authorized, error = check_authorization(post_id, user)
    # if not authorized:
    #     return response_payload(error, None)
    
    # Extract post_id and like_id from query parameters
    post_id = event['queryStringParameters'].get('post_id', '')
    like_id = event['queryStringParameters'].get('like_id', '')

    # Ensure at least one of post_id or like_id is provided
    if not post_id and not like_id:
        error_message = "Either post_id or like_id must be provided"
        logger.error(error_message)
        return response_payload(error_message, None)

    user = event["requestContext"]["authorizer"]["claims"]["sub"] | None
    
    try:
        if like_id:
            key = {'like_id': like_id, 'user': user}
            delete_condition = "Deleting like by like_id"
        elif post_id:
            key = {'post_id': post_id, 'user': user}
            delete_condition = "Deleting like by post_id"

        response = table.delete_item(Key=key)
        logger.info(f"like deleted successfully. {delete_condition}")
        return response_payload(None, 'like deleted successfully')
    except Exception as e:
        logger.error(f"Error delete like: {e}")
        return response_payload(f'Error deleting like: {e}', None)
    logger.info("Done deleting a new like")


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
