import json
import uuid
import boto3
from botocore.exceptions import ClientError
import logging
from datetime import datetime
from boto3.dynamodb.conditions import Attr

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
    user = "test"
    if "authorizer" in event["requestContext"]:
        user = event["requestContext"]["authorizer"]["claims"]["sub"]
    http_method = event['httpMethod']
    resource = event['resource']  # Get the resource from the event

    if http_method == 'GET':
        if resource == '/likes/add':
            return create_like(event, user)
        elif resource == '/likes/remove':
            return delete_like(event, user)
        elif resource == '/likes/mine':
            return list_likes(event, user)
        else:
            return response_payload("wrong url path", None)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return response_payload("Method Not Allowed", None)
        
def list_likes(event,user):
    logger.info("Listing all user likes")
    
    try:
        response = table.scan(
            FilterExpression=Attr('user').eq(user)
        )
        logger.info(f"Found {len(response['Items'])} likes for user {user}")
        return response_payload(None, response['Items'])
    except ClientError as e:
        logger.error(f"Error listing likes for user {user}: {e}")
        return response_payload(f'Error listing likes for user {user}: {e}', None)



def create_like(event,user):
    logger.info("Creating like")
    # Extract post_id from query parameters

    # Extract post_id and like_id from query parameters
    post_id = event['queryStringParameters'].get('post_id', '')
    comment_id = event['queryStringParameters'].get('comment_id', '')

    # Ensure at least one of post_id or like_id is provided
    if not post_id and not comment_id:
        error_message = "Either post_id or comment_id must be provided"
        logger.error(error_message)
        return response_payload(error_message, None)
    
    # Check if the user has already liked the post or comment
    # Check if the user has already liked the post or comment
    existing_like = None
    if post_id:
        existing_like = table.scan(
            FilterExpression=(
                Attr('post_id').eq(post_id) &
                Attr('user').eq(user)
            )
        )
    
    if comment_id:
        existing_like = table.scan(
            FilterExpression=(
                Attr('comment_id').eq(comment_id) &
                Attr('user').eq(user)
            )
        )
    
    if existing_like and existing_like.get('Items'):
        logger.info(f"User {user} has already liked the post {post_id} or comment {comment_id}")
        return response_payload("User has already liked this post or comment", None)

    id = str(uuid.uuid4())
    time_creation = datetime.utcnow().isoformat()
    
    try:
        table.put_item(Item={
        'id': id, 
        'post_id':post_id,
        'comment_id':comment_id,
        'time_creation': time_creation,
        'user': user, })
        logger.info(f"like created successfully with ID: {id}")
        return response_payload(None, 'like created successfully')
    except Exception as e:
        logger.error(f"Error creating like: {e}")
        return response_payload(f'Error creating like: {e}', None)
    logger.info("Done Creating a new like")


    
def delete_like(event,user):
    logger.info("Delete like")
    # authorized, error = check_authorization(post_id, user)
    # if not authorized:
    #     return response_payload(error, None)
    
    post_id = event['queryStringParameters'].get('post_id', '')
    comment_id = event['queryStringParameters'].get('comment_id', '')

    # Ensure at least one of post_id or like_id is provided
    if not post_id and not comment_id:
        error_message = "Either post_id or comment_id must be provided"
        logger.error(error_message)
        return response_payload(error_message, None)
    
    try:
        if comment_id:
            key = {'comment_id': comment_id, 'user': user}
            delete_condition = "Deleting like by comment_id"
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
