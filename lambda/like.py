import json
import uuid
import time
import boto3
from botocore.exceptions import ClientError
import logging
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key
# Set up logging
logger = logging.getLogger()
logger.setLevel("INFO")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('likes')

def generate_unique_like_id():
    timestamp = int(time.time() * 1000)  # Current time in milliseconds
    random_uuid = uuid.uuid4()  # Generate a random UUID
    unique_id = f"like_{timestamp}_{random_uuid}"
    return unique_id
    
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
        elif resource == '/likes/count':
            return count_likes(event)
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

def count_likes(event):
    logger.info("Fetch number of likes based on associated_id")

    query_string_parameters = event.get('queryStringParameters', {})

    # Check if query_string_parameters is None
    if query_string_parameters is None:
        query_string_parameters = {}

    # Extract post_id and comment_id from query parameters
    associated_id = query_string_parameters.get('associated_id', None)

    # Ensure at least one of post_id or comment_id is provided
    if not associated_id:
        error_message = "associated_id must be provided"
        logger.error(error_message)
        return response_payload(error_message, None)
    
    existing_like = None
    existing_like = table.scan(
        FilterExpression=(
            Attr('associated_id').eq(associated_id)
        )
    )
    
    if existing_like and existing_like.get('Items'):
        # return the number of likes
        num_likes = len(existing_likes['Items'])
        return response_payload(None, num_likes)
    else:
        # return 0 likes
        return response_payload(None, 0)

    logger.info("Done fetching the number of likes")

def create_like(event,user):
    logger.info("Creating like")
    # Extract post_id from query parameters
    # Extract post_id and comment_id from query parameters
    # Extract query string parameters safely
    query_string_parameters = event.get('queryStringParameters', {})

    # Check if query_string_parameters is None
    if query_string_parameters is None:
        query_string_parameters = {}

    # Extract post_id and comment_id from query parameters
    post_id = query_string_parameters.get('post_id', None)
    comment_id = query_string_parameters.get('comment_id', None)

    # Ensure at least one of post_id or comment_id is provided
    if not post_id and not comment_id:
        error_message = "Either post_id or comment_id must be provided"
        logger.error(error_message)
        return response_payload(error_message, None)
    
    # Check if the user has already liked the post or comment
    # Check if the user has already liked the post or comment
    
    post_or_comment_associated_id = post_id if post_id else comment_id
    logger.info(f"Using associated_id: {post_or_comment_associated_id}")
    
    existing_like = None
    existing_like = table.scan(
        FilterExpression=(
            Attr('associated_id').eq(post_or_comment_associated_id) &
            Attr('user').eq(user)
        )
    )
    
    if existing_like and existing_like.get('Items'):
        logger.info(f"User {user} has already liked the post {post_id} or comment {comment_id}")
        return response_payload("User has already liked this post or comment", None)

    id = str(generate_unique_like_id())
    time_creation = datetime.utcnow().isoformat()
    
    try:
        table.put_item(Item={
        'id': id, 
        'associated_id':post_or_comment_associated_id,
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
    
    query_string_parameters = event.get('queryStringParameters', {})

    # Check if query_string_parameters is None
    if query_string_parameters is None:
        query_string_parameters = {}

    # Extract post_id and comment_id from query parameters
    post_id = query_string_parameters.get('post_id', None)
    comment_id = query_string_parameters.get('comment_id', None)

    # Ensure at least one of post_id or like_id is provided
    if not post_id and not comment_id:
        error_message = "Either post_id or comment_id must be provided"
        logger.error(error_message)
        return response_payload(error_message, None)
        
    post_or_comment_associated_id = None
    if comment_id:
        post_or_comment_associated_id = comment_id
    if post_id:
        post_or_comment_associated_id = post_id
        
    # delete
    # Step 1: Query to get the partition key
    response = table.scan(
        FilterExpression=Key('associated_id').eq(post_or_comment_associated_id) & 
        Attr("user").eq(user)
    )
    
    items = response.get('Items', [])
    
    if not items:
        logger.error("No items found with the given sort key and attribute.")
        return response_payload(f'Error deleting like, item not found', None)
    else:
        # Assuming the partition key is 'partitionKey'
        partition_key_value = items[0]['id']
    
        # Step 2: Delete the item using the partition key and sort key
        try:
            table.delete_item(
                Key={
                    'id': partition_key_value,
                    'associated_id': post_or_comment_associated_id
                }
            )
            logger.info(f"like deleted successfully.")
            return response_payload(None, 'like deleted successfully')
        except Exception as e:
            logger.error(f"Error delete like: {e}")
            return response_payload(f'Error deleting like: {e}', None)
    
    # try:
    #     key = {'associated_id': post_or_comment_associated_id, 'user': user}
    #     delete_condition = f"associated_id :  {post_or_comment_associated_id}"
    #     response = table.delete_item(Key=key)
    #     logger.info(f"like deleted successfully. {delete_condition}")
    #     return response_payload(None, 'like deleted successfully')
    # except Exception as e:
    #     logger.error(f"Error delete like: {e}")
    #     return response_payload(f'Error deleting like: {e}', None)
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
