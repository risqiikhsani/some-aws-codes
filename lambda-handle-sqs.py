import json
import boto3
from boto3.dynamodb.conditions import Key
import os
# Initialize DynamoDB and SQS resources
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def lambda_handler(event, context):
    print("event = ")
    print(event)
    for record in event['Records']:
        print("records =")
        print(record)
        
        # Extracting the body and parsing it as JSON
        body = json.loads(record["body"])
        message = json.loads(body["Message"])
        # Check if the message is an S3 event notification
        if "Records" in message:
            print("Records in message")
            print(message)
            # Extracting the bucket name and object key
            bucket_name = message["Records"][0]["s3"]["bucket"]["name"]
            object_key = message["Records"][0]["s3"]["object"]["key"]
            event_time = message["Records"][0]["eventTime"]
            print("result : ")
            print(bucket_name)
            print(object_key)
            print(event_time)
            
            # Save the image information to the DynamoDB table
            try:
                table.put_item(
                    Item={
                        'id': record['messageId'],
                        'Bucket': bucket_name,
                        'ObjectKey': object_key,
                        'EventTime': event_time
                    }
                )
                print(f"Image information saved to DynamoDB: Bucket={bucket_name}, ObjectKey={object_key}, EventTime={event_time}")
            except Exception as e:
                print(f"Error saving image information to DynamoDB: {e}")
        else:
            print("Records not in message")
            print(message)
            # Delete the message from the SQS queue
            receipt_handle = record['receiptHandle']
            sqs.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=receipt_handle
            )
            
            # Log the delete operation
            print(f'Message deleted from SQS queue')
            pass
        
        # Delete the message from the SQS queue
        receipt_handle = record['receiptHandle']
        sqs.delete_message(
            QueueUrl=SQS_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )
        
        # Log the delete operation
        print(f'Message deleted from SQS queue')

    return {
        'statusCode': 200,
        'body': json.dumps('Image information saved to DynamoDB')
    }

# {
#   "messageId": "ee473db6-ac09-4791-8370-9685a724fb6e",
#   "receiptHandle": "AQEBmSuUxtnb/MoMTl8tT7aXXbTjHTwq6zYl3D9RRbjJ12qAhEO+guBCEuFeeYeuQBF9VLtijL304WwhAd6t4eSAVDnJu5fQ2LFL7nXcZbCmVPlXW6gmfBgz1E+YPZCATg/X3gDfXys84EIAcwE0qs5H1Qbsax8lE109sdna/DAXGHn7Zh0G27dNzJueFmiBHzlU7YZ5YLtuBUfyZN+sii7yKdm8myRwLmZgN+/VjeDEym/WKngTUDzjV8y1biqomRgIQh87Ob9+hwvX/+vyWOfzalaHT+BwPkWNF+NUaCUqiX8hxs2UohLZJ6k9pCh4ack0zQUG4+MAYfCmBTYSDf8ytq8tXRUElQEZTCEwMyW5hrK8RKcxGl0GBnKvoSYwkRWh",
#   "body": "{\n  \"Type\" : \"Notification\",\n  \"MessageId\" : \"4bed3d00-7b8a-57fd-af36-63caedac7839\",\n  \"TopicArn\" : \"arn:aws:sns:us-east-1:259908435287:s3-topic\",\n  \"Subject\" : \"Amazon S3 Notification\",\n  \"Message\" : \"{\\\"Records\\\":[{\\\"eventVersion\\\":\\\"2.1\\\",\\\"eventSource\\\":\\\"aws:s3\\\",\\\"awsRegion\\\":\\\"us-east-1\\\",\\\"eventTime\\\":\\\"2024-05-24T13:19:33.457Z\\\",\\\"eventName\\\":\\\"ObjectCreated:Put\\\",\\\"userIdentity\\\":{\\\"principalId\\\":\\\"AWS:AROATZA577VL635RFEKYA:user2740971=RISQI_IKHSANI\\\"},\\\"requestParameters\\\":{\\\"sourceIPAddress\\\":\\\"125.160.103.164\\\"},\\\"responseElements\\\":{\\\"x-amz-request-id\\\":\\\"XEE1DKFYCYT4S40K\\\",\\\"x-amz-id-2\\\":\\\"jenXm58knX9IkOvs2YFzSYd19fyJoZlkW8F7k2R4BlYhUl9nRb17UazWFAxmo8pV287wtwBf0KLk8V//HcK7ieppYyIR8fS5QntmACfGfB0=\\\"},\\\"s3\\\":{\\\"s3SchemaVersion\\\":\\\"1.0\\\",\\\"configurationId\\\":\\\"s3event\\\",\\\"bucket\\\":{\\\"name\\\":\\\"randomimagesbucket\\\",\\\"ownerIdentity\\\":{\\\"principalId\\\":\\\"A3KX1JD2LP2OFE\\\"},\\\"arn\\\":\\\"arn:aws:s3:::randomimagesbucket\\\"},\\\"object\\\":{\\\"key\\\":\\\"fungus+ringworm+face+TAS.jpg\\\",\\\"size\\\":14544,\\\"eTag\\\":\\\"88d1484b7856e1fd6fc446c4fdb22776\\\",\\\"sequencer\\\":\\\"00665093E5680E2E8D\\\"}}}]}\",\n  \"Timestamp\" : \"2024-05-24T13:19:34.073Z\",\n  \"SignatureVersion\" : \"1\",\n  \"Signature\" : \"F8uxg0txkcVfNkr69G9+BOrJDp/+bn83mQH+ye/BRVamo5Qs5nYlZWtixAURTQ1CVwR+vGuFIoLk39E/xcHqFjefPMN8n7OOQXc173q7JPKPVGTPtUtqdjn1dzr27PigLW07fn2ufZQ1g2N8J9lqwWyu4x69C5p+a9KQkFsmLScymGxyEXV3HIIXI+S3XDd8nB4FkFDBW+86ZFB+lB94XQQ08NUPw+IyZZngrH4bsDZthPM0y7DEmufGfctZMCaURv1//dnDks09szmGD0B7S+y0nYUhE8oribmBcIgsX4ABiqQNPypefkSFDsjAdwe6VDCIeI7AyIrcF66kMGJL7A==\",\n  \"SigningCertURL\" : \"https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem\",\n  \"UnsubscribeURL\" : \"https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:259908435287:s3-topic:7a12ebf3-211e-4261-8d37-85e384032cf6\"\n}",
#   "attributes": {
#     "ApproximateReceiveCount": "20",
#     "SentTimestamp": "1716556774109",
#     "SenderId": "AIDAIT2UOQQY3AUEKVGXU",
#     "ApproximateFirstReceiveTimestamp": "1716556774111"
#   },
#   "messageAttributes": {},
#   "md5OfBody": "ddd672f80461f50468ca1e0ff8e58f92",
#   "eventSource": "aws:sqs",
#   "eventSourceARN": "arn:aws:sqs:us-east-1:259908435287:app-queue",
#   "awsRegion": "us-east-1"
# }


# Message body from s3: 
# {
#     "Records": [
#         {
#             "eventVersion": "2.1",
#             "eventSource": "aws:s3",
#             "awsRegion": "us-east-1",
#             "eventTime": "2024-05-18T05:41:02.223Z",
#             "eventName": "ObjectCreated:Put",
#             "userIdentity": {
#                 "principalId": "AWS:AROATZA577VL635RFEKYA:user2740971=RISQI_IKHSANI"
#             },
#             "requestParameters": {
#                 "sourceIPAddress": "125.163.246.218"
#             },
#             "responseElements": {
#                 "x-amz-request-id": "MA18E2F5YA1JFARD",
#                 "x-amz-id-2": "WPAw+Sib+IwZb5htwcbQYyl6MlHdzfENsL24A2dOsy3dwNqm7DU68k2Vr8a+R1Kf+Fc7HhbgJN+PTyPmw1/PquIFYwA5M7YR"
#             },
#             "s3": {
#                 "s3SchemaVersion": "1.0",
#                 "configurationId": "RekognitionEvent",
#                 "bucket": {
#                     "name": "randomimagesbucket",
#                     "ownerIdentity": {
#                         "principalId": "A3KX1JD2LP2OFE"
#                     },
#                     "arn": "arn:aws:s3:::randomimagesbucket"
#                 },
#                 "object": {
#                     "key": "fungus+ringworm+face+TAS.jpg",
#                     "size": 14544,
#                     "eTag": "88d1484b7856e1fd6fc446c4fdb22776",
#                     "sequencer": "0066483F6E1E8C6F5F"
#                 }
#             }
#         }
#     ]
# }

# def lambda_handler(event, context):
#     table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    
#     for record in event['Records']:
#         # Extract message ID and body
#         message_id = record['messageId']
#         message_body = record['body']
        
#         # Log the received message
#         print(f'Received message ID: {message_id}')
#         print(f'Message body: {message_body}')
        
#         # Parse the message body
#         message_body_json = json.loads(message_body)
#         print(f'Parsed message body: {message_body_json}')
        
#         # Extract the S3 object key and bucket name
#         s3_object_key = message_body_json['Records'][0]['s3']['object']['key']
#         s3_bucket_name = message_body_json['Records'][0]['s3']['bucket']['name']
        
#         print(f'S3 bucket: {s3_bucket_name}')
#         print(f'S3 object key: {s3_object_key}')
        
#         # Save message to DynamoDB
#         table.put_item(
#             Item={
#                 'id': message_id,
#                 'ProcessedImage': s3_object_key
#             }
#         )
        
#         # Log the save operation
#         print(f'Message saved to DynamoDB table {DYNAMODB_TABLE_NAME}')
        
#         # Delete the message from the queue
#         receipt_handle = record['receiptHandle']
#         sqs.delete_message(
#             QueueUrl=SQS_QUEUE_URL,
#             ReceiptHandle=receipt_handle
#         )
        
#         # Log the delete operation
#         print(f'Message ID {message_id} deleted from SQS queue')
    
#     return {
#         'statusCode': 200,
#         'body': json.dumps('Messages processed successfully')
#     }



