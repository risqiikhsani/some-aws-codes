import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Create the Rekognition client
    rekognition = boto3.client('rekognition')
    
    try:
        # Call the DetectLabels operation
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=10,
            MinConfidence=70
        )
        
        # Prepare the response for API Gateway
        api_response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
                "labels": [
                    {
                        "name": label['Name'],
                        "confidence": label['Confidence']
                    } for label in response['Labels']
                ]
            }
        }
        
        return api_response
    
    except ClientError as e:
        print(e)
        return {
            "statusCode": 500,
            "body": str(e)
        }
    
# bedrock
import os
import json
import boto3
from langchain.llms import BedrockedLLM
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationEntityMemory

def lambda_handler(event, context):
    # Initialize the Bedrock client
    bedrock = boto3.client('bedrock')

    # Create the Bedrock-powered LLM
    llm = BedrockedLLM(
        bedrock_client=bedrock,
        model_name='claude-v3',
        temperature=0.7,
        max_tokens=1024
    )

    # Define a prompt template for healthcare-related tasks
    healthcare_prompt = PromptTemplate(
        input_variables=["history", "query"],
        template="You are an AI assistant specializing in healthcare. The conversation history is: {history}. Please provide a response to the following query: {query}"
    )

    # Get the user's message and user ID from the event
    user_message = event['message']
    user_id = event['user_id']

    # Create the conversation memory for the user
    conversation_memory = ConversationEntityMemory(k=5, entity_key="user_id")
    conversation_memory.save_context({"user_id": user_id}, user_message)

    # Create the ConversationChain with the healthcare prompt and memory
    healthcare_chain = ConversationChain(
        llm=llm,
        prompt=healthcare_prompt,
        memory=conversation_memory
    )

    # Generate a response using the healthcare chain
    response = healthcare_chain.predict(input=user_message)

    # Update the conversation memory
    healthcare_chain.save_context({"query": user_message, "user_id": user_id}, response)

    # Prepare the response for API Gateway
    api_response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "response": response
        })
    }

    return api_response

