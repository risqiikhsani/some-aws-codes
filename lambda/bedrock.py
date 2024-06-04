import json
import boto3

# Let's use Amazon S3
bedrock_runtime = boto3.client('bedrock-runtime')

def invoke_model(body, model_id, accept, content_type):
    """
    Invokes Amazon bedrock model to run an inference
    using the input provided in the request body.
    
    Args:
        body (dict): The invokation body to send to bedrock
        model_id (str): the model to query
        accept (str): input accept type
        content_type (str): content type
    Returns:
        Inference response from the model.
    """

    try:
        response = bedrock_runtime.invoke_model(
            body=json.dumps(body), 
            modelId=model_id, 
            accept=accept, 
            contentType=content_type
        )

        return response

    except Exception as e:
        print(f"Couldn't invoke {model_id}")
        raise e


# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html
def lambda_handler(event, context):
    body = json.loads(event["body"])
    messages = body["messages"]
    
    # messages
    # [
    #   {"role": "user", "content": "Hello there."},
    #   {"role": "assistant", "content": "Hi, I'm Claude. How can I help you?"},
    #   {"role": "user", "content": "Can you explain LLMs in plain English?"},
    # ]
    
    system_prompt = "You are BOT from website called Health4Us, an AI assistant to be helpful,harmless, and honest about healthcare. Your goal is to provide informative and substantive responses to queries related to healthcare only , while avoiding potential harms. example , if user provides a symptoms , you will answer the most likely cause or disease name and how to prevent it. if user provides a disease name , you can answer about the symptoms and how to prevent it, etc. "
    max_tokens=1000
    # user_message =  {"role": "user", "content": text}
    # messages = [user_message]
    body={
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages
    }  
 
    modelId = "anthropic.claude-3-haiku-20240307-v1:0"  # change this to use a different version from the model provider
    accept = "application/json"
    contentType = "application/json"
    
    response = invoke_model(body, modelId, accept, contentType)
    print(response)
    response_body = json.loads(response.get("body").read())
    print(response_body.get("content"))
    # print(response_body.get("completion"))
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(response_body.get("content"))
    }
