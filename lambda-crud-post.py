import json
import uuid
import boto3
from botocore.exceptions import ClientError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Posts')
s3 = boto3.client('s3')
bucket_name = 'XXXXXXXXXXXXXXXXXXX'

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    http_method = event['httpMethod']
    if http_method == 'POST':
        return create_post(event)
    elif http_method == 'GET':
        if event['pathParameter'] and 'id' in event['pathParameter']:
            return get_post(event)
        else:
            return list_posts()
    elif http_method == 'PUT':
        return update_post(event)
    elif http_method == 'DELETE':
        return delete_post(event)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return {
            'statusCode': 405,
            'body': json.dumps('Method Not Allowed')
        }


def create_post(event):
    logger.info("Creating a new post")
    body = json.loads(event['body'])
    post_id = str(uuid.uuid4())
    text = body['text']
    user = body['user']
    
    try:
        table.put_item(Item={'id': post_id, 'text': text, 'user': user, 'image_name': post_id})
        logger.info(f"Post created successfully with ID: {post_id}")
        return {
            'statusCode': 201,
            'body': json.dumps('Post created successfully')
        }
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error creating post: {e}')
        }

def get_post(event):
    logger.info("Getting a post")
    post_id = event['pathParameter']['id']
    
    try:
        response = table.get_item(Key={'id': post_id})
        if 'Item' in response:
            logger.info(f"Post found with ID: {post_id}")
            return {
                'statusCode': 200,
                'body': json.dumps(response['Item'])
            }
        else:
            logger.info(f"Post not found with ID: {post_id}")
            return {
                'statusCode': 404,
                'body': json.dumps('Post not found')
            }
    except ClientError as e:
        logger.error(f"Error getting post: {e}")

def list_posts():
    logger.info("Listing all posts")
    try:
        response = table.scan()
        logger.info(f"Found {len(response['Items'])} posts")
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'])
        }
    except ClientError as e:
        logger.error(f"Error listing posts: {e}")

def update_post(event):
    logger.info("Updating a post")
    body = json.loads(event['body'])
    post_id = event['pathParameter']['id']
    text = body['text']
    user = body['user']
    
    try:
        table.update_item(
            Key={'id': post_id},
            UpdateExpression='SET text = :text, user = :user',
            ExpressionAttributeValues={':text': text, ':user': user}
        )
        logger.info(f"Post updated successfully with ID: {post_id}")
        return {
            'statusCode': 200,
            'body': json.dumps('Post updated successfully')
        }
    except Exception as e:
        logger.error(f"Error updating post: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error updating post: {e}')
        }

def delete_post(event):
    logger.info("Deleting a post")
    post_id = event['pathParameter']['id']
    
    try:
        table.delete_item(Key={'id': post_id})
        logger.info(f"Post deleted successfully with ID: {post_id}")
        return {
            'statusCode': 200,
            'body': json.dumps('Post deleted successfully')
        }
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error deleting post: {e}')
        }
