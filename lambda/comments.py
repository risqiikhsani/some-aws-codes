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
table = dynamodb.Table('comments')

def check_authorization(comment_id, user):
    logger.info("Checking user authorization")
    try:
        # Retrieve the comment to check ownership
        response = table.get_item(Key={'id': comment_id})
        if 'Item' not in response:
            logger.info(f"comment not found with ID: {comment_id}")
            return False, 'comment not found'

        comment = response['Item']
        if comment['user'] != user:
            logger.warning(f"User {user} is not authorized to modify comment with ID: {comment_id}")
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
    if http_method == 'POST':
        return create_comment(event,user)
    elif http_method == 'GET':
        if 'pathParameters' in event and event['pathParameters'] is not None and 'id' in event['pathParameters']:
            return get_comment(event)
        else:
            return list_comments(event)
    elif http_method == 'PUT':
        return update_comment(event,user)
    elif http_method == 'DELETE':
        return delete_comment(event,user)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return response_payload("Method Not Allowed", None)


def create_comment(event,user):
    logger.info("Creating a new comment")
    # Extract post_id from query parameters
    if event.get('queryStringParameters') is not None:
        try:
            post_id = event['queryStringParameters']['post_id']
        except KeyError:
            error_message = "post_id not provided in the query parameters"
            logger.error(error_message)
            return response_payload(error_message, None)
    else:
        error_message = "queryStringParameters not provided in the event"
        logger.error(error_message)
        return response_payload(error_message, None)
    
    data = json.loads(event['body'])
    comment_id = str(uuid.uuid4())
    text = data['text']
    time_creation = datetime.utcnow().isoformat()
    
    try:
        table.put_item(Item={
        'id': comment_id, 
        'text': text, 
        'post_id':post_id,
        'time_creation':time_creation,
        'user': user, })
        logger.info(f"comment created successfully with ID: {comment_id}")
        return response_payload(None, 'comment created successfully')
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        return response_payload(f'Error creating comment: {e}', None)
    logger.info("Done Creating a new comment")


def get_comment(event):
    logger.info("Getting a comment")
    comment_id = event['pathParameters']['id']
    
    try:
        response = table.get_item(Key={'id': comment_id})
        if 'Item' in response:
            logger.info(f"comment found with ID: {comment_id}")
            return response_payload(None, response['Item'])
        else:
            logger.info(f"comment not found with ID: {comment_id}")
            return response_payload('comment not found', None)
    except ClientError as e:
        logger.error(f"Error getting comment: {e}")
        return response_payload(f'Error getting comment: {e}', None)
    logger.info("Done getting a comment")


def list_comments(event):
    logger.info("Listing all comments")
    # Extract post_id from query parameters
    if event.get('queryStringParameters') is not None:
        try:
            post_id = event['queryStringParameters']['post_id']
        except KeyError:
            error_message = "post_id not provided in the query parameters"
            logger.error(error_message)
            return response_payload(error_message, None)
    else:
        error_message = "queryStringParameters not provided in the event"
        logger.error(error_message)
        return response_payload(error_message, None)

    try:
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('post_id').eq(post_id)
        )
        logger.info(f"Found {len(response['Items'])} comments")
        return response_payload(None, response['Items'])
    except ClientError as e:
        logger.error(f"Error listing comments: {e}")
        return response_payload(f'Error listing comments: {e}', None)
    logger.info("Done listing all comments")


def update_comment(event,user):
    logger.info("Updating a comment")
    data = json.loads(event['body'])
    comment_id = event['pathParameters']['id']
    
    # authorized, error = check_authorization(comment_id, user)
    # if not authorized:
    #     return response_payload(error, None)
    
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
            Key={'id': comment_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"comment updated successfully with ID: {comment_id}")
        return response_payload(None,'comment updated successfully')
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        return response_payload(f'Error updating comment: {e}', None)
    logger.info("Done updating a comment")


def delete_comment(event,user):
    logger.info("Deleting a comment")
    comment_id = event['pathParameters']['id']
    
    # authorized, error = check_authorization(comment_id, user)
    # if not authorized:
    #     return response_payload(error, None)
    
    try:
        table.delete_item(Key={'id': comment_id})
        logger.info(f"comment deleted successfully with ID: {comment_id}")
        return response_payload(None, 'comment deleted successfully')
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        return response_payload(f'Error deleting comment: {e}', None)
    logger.info("Done deleting a comment")


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
