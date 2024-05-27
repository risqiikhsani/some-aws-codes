import logging

# Configure the logger
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def lambda_handler(event, context):
    # Log messages with different levels
    logging.debug('This is a debug message')
    logging.info('This is an informational message')
    logging.warning('This is a warning message')
    logging.error('This is an error message')
    logging.critical('This is a critical message')

    # Your function logic here
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
