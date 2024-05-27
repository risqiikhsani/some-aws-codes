import json
import uuid
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Comments')

def lambda_handler(event, context):
    http_method = event['httpMethod']
    if http_method == 'POST':
        return create_comment(event)
    elif http_method == 'GET':
        if event['queryStringParameters'] and 'id' in event['queryStringParameters']:
            return get_comment(event)
        elif event['queryStringParameters'] and 'post_id' in event['queryStringParameters']:
            return list_comments(event)
    elif http_method == 'PUT':
        return update_comment(event)
    elif http_method == 'DELETE':
        return delete_comment(event)
    else:
        return {
            'statusCode': 405,
            'body': json.dumps('Method Not Allowed')
        }

def create_comment(event):
    body = json.loads(event['body'])
    comment_id = str(uuid.uuid4())
    post_id = body['post_id']
    text = body['text']
    user = body['user']
    
    table.put_item(Item={'id': comment_id, 'post_id': post_id, 'text': text, 'user': user})
    
    return {
        'statusCode': 201,
        'body': json.dumps('Comment created successfully')
    }

def get_comment(event):
    comment_id = event['queryStringParameters']['id']
    
    try:
        response = table.get_item(Key={'id': comment_id})
    except ClientError as e:
        return {
            'statusCode': 400,
            'body': json.dumps(e.response['Error']['Message'])
        }
    
    if 'Item' not in response:
        return {
            'statusCode': 404,
            'body': json.dumps('Comment not found')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps(response['Item'])
    }

def list_comments(event):
    post_id = event['queryStringParameters']['post_id']
    
    try:
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('post_id').eq(post_id)
        )
    except ClientError as e:
        return {
            'statusCode': 400,
            'body': json.dumps(e.response['Error']['Message'])
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps(response['Items'])
    }

def update_comment(event):
    body = json.loads(event['body'])
    comment_id = event['queryStringParameters']['id']
    post_id = body['post_id']
    text = body['text']
    user = body['user']
    
    table.update_item(
        Key={'id': comment_id},
        UpdateExpression='SET post_id = :post_id, text = :text, user = :user',
        ExpressionAttributeValues={':post_id': post_id, ':text': text, ':user': user}
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Comment updated successfully')
    }

def delete_comment(event):
    comment_id = event['queryStringParameters']['id']
    
    table.delete_item(Key={'id': comment_id})
    
    return {
        'statusCode': 200,
        'body': json.dumps('Comment deleted successfully')
    }

