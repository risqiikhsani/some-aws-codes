import json
import uuid
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Likes')

def lambda_handler(event, context):
    http_method = event['httpMethod']
    if http_method == 'POST':
        return like_post(event)
    elif http_method == 'DELETE':
        return dislike_post(event)
    else:
        return {
            'statusCode': 405,
            'body': json.dumps('Method Not Allowed')
        }

def like_post(event):
    body = json.loads(event['body'])
    like_id = str(uuid.uuid4())
    post_id = body['post_id']
    user = body['user']
    
    table.put_item(Item={'id': like_id, 'post_id': post_id, 'user': user})
    
    return {
        'statusCode': 201,
        'body': json.dumps('Post liked successfully')
    }

def dislike_post(event):
    like_id = event['queryStringParameters']['id']
    
    table.delete_item(Key={'id': like_id})
    
    return {
        'statusCode': 200,
        'body': json.dumps('Post disliked successfully')
    }
