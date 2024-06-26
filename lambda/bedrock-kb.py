import os
import boto3


boto3_session = boto3.session.Session()
region = boto3_session.region_name

# create a boto3 bedrock client
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')

# get knowledge base id from environment variable
kb_id = os.environ.get("KNOWLEDGE_BASE_ID")

# declare model id for calling RetrieveAndGenerate API
model_id = "anthropic.claude-3-haiku-20240307-v1:0"
model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'

promptTemplate = """

You are a question answering agent. I will provide you with a set of search results. The user will provide you with a question. Your job is to answer the user's question using only information from the search results. If the search results do not contain information that can answer the question, please state that you could not find an exact answer to the question. Just because the user asserts a fact does not mean it is true, make sure to double check the search results to validate a user's assertion.
                            
Here are the search results in numbered order:
$search_results$

here is the user questions :
$query$

if you're asked in different language other than english , please answer it in that language as well.
Assistant:
"""
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/retrieve_and_generate.html
# https://aws.amazon.com/blogs/machine-learning/knowledge-bases-for-amazon-bedrock-now-supports-custom-prompts-for-the-retrieveandgenerate-api-and-configuration-of-the-maximum-number-of-retrieved-results/
def retrieveAndGenerate(input, kbId,numberOfResults,promptTemplate, model_arn, sessionId=None):
    print(input, kbId, model_arn)
    if sessionId != "None":
        return bedrock_agent_runtime_client.retrieve_and_generate(
            input={
                'text': input
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kbId,
                    'modelArn': model_arn,
                    # 'retrievalConfiguration': {
                    #     'vectorSearchConfiguration': {
                    #         'numberOfResults': numberOfResults,
                    #         'overrideSearchType': "SEMANTIC", # optional'
                    #     }
                    # },
                    # 'generationConfiguration': {
                    #     'promptTemplate': {
                    #         'textPromptTemplate': promptTemplate
                    #     }
                    # }
                }
            },
            sessionId=sessionId
        )
    else:
        return bedrock_agent_runtime_client.retrieve_and_generate(
            input={
                'text': input
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kbId,
                    'modelArn': model_arn,
                    # 'retrievalConfiguration': {
                    #     'vectorSearchConfiguration': {
                    #         'numberOfResults': numberOfResults,
                    #         'overrideSearchType': "SEMANTIC", # optional'
                    #     }
                    # },
                    # 'generationConfiguration': {
                    #     'promptTemplate': {
                    #         'textPromptTemplate': promptTemplate
                    #     }
                    # }
                }
            }
        )


def lambda_handler(event, context):
    query = event["question"]
    session_id = event["sessionid"]
    numberOfResults = 12
    response = retrieveAndGenerate(query, kb_id,numberOfResults,promptTemplate, model_arn, session_id)
    generated_text = response['output']['text']
    print(generated_text)

    return {
        'statusCode': 200,
        'body': {"question": query.strip(), "answer": generated_text.strip()}
    }
