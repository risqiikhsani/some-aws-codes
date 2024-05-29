import json
import uuid
import boto3
from botocore.exceptions import ClientError
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel("INFO")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('posts')


def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    http_method = event['httpMethod']
    if http_method == 'POST':
        return create_post(event)
    elif http_method == 'GET':
        if 'pathParameters' in event and event['pathParameters'] is not None and 'id' in event['pathParameters']:
            return get_post(event)
        else:
            return list_posts()
    elif http_method == 'PUT':
        return update_post(event)
    elif http_method == 'DELETE':
        return delete_post(event)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return response_payload("Method Not Allowed", None)


def create_post(event):
    logger.info("Creating a new post")
    data = json.loads(event['body'])
    post_id = str(uuid.uuid4())
    text = data['text']
    user = "usertest"
    
    try:
        table.put_item(Item={
        'id': post_id, 
        'text': text, 
        'user': user, })
        logger.info(f"Post created successfully with ID: {post_id}")
        return response_payload(None, 'Post created successfully')
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return response_payload(f'Error creating post: {e}', None)


def get_post(event):
    logger.info("Getting a post")
    post_id = event['pathParameters']['id']
    
    try:
        response = table.get_item(Key={'id': post_id})
        if 'Item' in response:
            logger.info(f"Post found with ID: {post_id}")
            return response_payload(None, response['Item'])
        else:
            logger.info(f"Post not found with ID: {post_id}")
            return response_payload('Post not found', None)
    except ClientError as e:
        logger.error(f"Error getting post: {e}")
        return response_payload(f'Error getting post: {e}', None)


def list_posts():
    logger.info("Listing all posts")
    try:
        response = table.scan()
        logger.info(f"Found {len(response['Items'])} posts")
        return response_payload(None, response['Items'])
    except ClientError as e:
        logger.error(f"Error listing posts: {e}")
        return response_payload(f'Error listing posts: {e}', None)


def update_post(event):
    logger.info("Updating a post")
    data = json.loads(event['body'])
    post_id = event['pathParameters']['id']
    # text = body['text']
    # user = body['user']
    
    update_expression = "SET "
    expression_attribute_values = {}
    expression_attribute_names = {}
    for key, value in data.items():
        safe_key = f"#{key}"
        update_expression += f"{safe_key} = :{key}, "
        expression_attribute_names[safe_key] = key
        expression_attribute_values[f":{key}"] = value
    
    # Remove trailing comma and space
    update_expression = update_expression.rstrip(", ")
    
    try:
        response = table.update_item(
            Key={'id': post_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"Post updated successfully with ID: {post_id}")
        return response_payload(None,'Post updated successfully')
    except Exception as e:
        logger.error(f"Error updating post: {e}")
        return response_payload(f'Error updating post: {e}', None)


def delete_post(event):
    logger.info("Deleting a post")
    post_id = event['pathParameters']['id']
    
    try:
        table.delete_item(Key={'id': post_id})
        logger.info(f"Post deleted successfully with ID: {post_id}")
        return response_payload(None, 'Post deleted successfully')
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return response_payload(f'Error deleting post: {e}', None)


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
