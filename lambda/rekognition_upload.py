import json
import boto3
import logging
import base64
import uuid
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel("INFO")

s3 = boto3.client('s3')
BUCKET_NAME = 'myapp-images-bucket'

def upload_image_to_s3(user_id, data):
    image_data = data.pop("image", None)
    
    try:
        image_decoded = base64.b64decode(image_data)
        image_key = f"image_rekognition/{user_id}/{uuid.uuid4()}.jpg"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=image_key,
            Body=image_decoded,
            ContentType='image/jpeg'
        )
        image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_key}"
        logger.info(f"Image uploaded successfully to {image_url}")
        return response_payload(None, {"image_url": image_url, "image_key": image_key})
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return response_payload(e)
        
        
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

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    user = "test"
    if "authorizer" in event["requestContext"]:
        user = event["requestContext"]["authorizer"]["claims"]["sub"]
        
    http_method = event['httpMethod']
    if http_method == 'POST':
        data = json.loads(event["body"])
        return upload_image_to_s3(user,data)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return response_payload("Method Not Allowed")
