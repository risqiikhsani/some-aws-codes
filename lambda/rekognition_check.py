import json
import boto3
import logging

client = boto3.client('rekognition')
logger = logging.getLogger()
logger.setLevel("INFO")

PROJECT_ARN = 'arn:aws:rekognition:ap-southeast-2:730335214792:project/skin-diseases/1718021845211'
VERSION_NAME = 'skin-diseases.2024-06-11T10.24.49'

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

def check_model(project_arn, version_name):
    logger.info("check model...")
    try:
        # Get the running status
        describe_response = client.describe_project_versions(ProjectArn=project_arn, VersionNames=[version_name])
        print(describe_response)
        for model in describe_response['ProjectVersionDescriptions']:
            status = model['Status']
            status_message = model['StatusMessage']
            logger.info(f"Status: {status}")
            logger.info(f"Message: {status_message}")
            return response_payload(None, {"Status": status, "StatusMessage": status_message})
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
        return check_model(PROJECT_ARN, VERSION_NAME)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return response_payload("Method Not Allowed")

