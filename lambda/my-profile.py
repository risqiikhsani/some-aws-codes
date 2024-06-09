import json
import uuid
import boto3
from botocore.exceptions import ClientError
import logging
import base64

# Set up logging
logger = logging.getLogger()
logger.setLevel("INFO")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

s3 = boto3.client('s3')
BUCKET_NAME = 'myapp-images-bucket'  # Replace with your S3 bucket name


def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    user = "test"
    if "authorizer" in event["requestContext"]:
        print(event["requestContext"]["authorizer"]["claims"]["sub"])
        user = event["requestContext"]["authorizer"]["claims"]["sub"]
    
    http_method = event['httpMethod']
    if http_method == 'GET':
        return get_user(user)
    elif http_method == 'PUT':
        data = json.loads(event['body'])
        return update_user(user,data)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return response_payload("Method Not Allowed", None)

def get_user(user):
    logger.info("Getting a user")
    try:
        response = table.get_item(Key={'id': user})
        if 'Item' in response:
            logger.info(f"User found with ID: {user}")
            return response_payload(None, response['Item'])
        else:
            logger.info(f"User not found with ID: {user}")
            return response_payload('User not found', None)
    except ClientError as e:
        logger.error(f"Error getting post: {e}")
        return response_payload(f'Error getting user: {e}', None)

def update_user(user,data):
    logger.info("Updating a user")
    
    # Check if there is an image to upload
    image_data = data.pop("profile_image", None)
    if image_data:
        image_url = upload_image_to_s3(user, image_data)
        data["profile_image_url"] = image_url

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
            Key={'id': user},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"User updated successfully with ID: {user}")
        return response_payload(None,'User updated successfully')
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return response_payload(f'Error updating user: {e}', None)

def upload_image_to_s3(user_id, image_data):
    try:
        image_decoded = base64.b64decode(image_data)
        image_key = f"profile_images/{user_id}/{uuid.uuid4()}.jpg"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=image_key,
            Body=image_decoded,
            ContentType='image/jpeg'
        )
        image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_key}"
        logger.info(f"Image uploaded successfully to {image_url}")
        return image_url
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise e



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
