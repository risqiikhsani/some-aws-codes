import boto3
from botocore.exceptions import ClientError
import logging
import json
import uuid

# Configure the logger
logging = logging.getLogger()
logging.setLevel("INFO")

session = boto3.Session()
dynamodb = session.resource("dynamodb")

# Define the table name and schema
table_name = "Items"
table = dynamodb.Table(table_name)

# Function to create an item in the table
def create_item(data):
    try:
        data["id"] = str(uuid.uuid4())  # Generate a unique ID for the item
        table.put_item(Item=data)
        logging.info("Item created successfully")
        return {"statusCode": 200, "body": json.dumps("Item created successfully")}
    except ClientError as e:
        logging.error(f"Error creating item: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Error creating item: {e}")}

# Function to get an item from the table
def get_item(item_id):
    try:
        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")
        if item:
            logging.info(f"Item found: {item}")
            return {"statusCode": 200, "body": json.dumps(item)}
        else:
            logging.info(f"Item not found: {item_id}")
            return {"statusCode": 404, "body": json.dumps("Item not found")}
    except ClientError as e:
        logging.error(f"Error getting item: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Error getting item: {e}")}

# Function to get all items from the table
def get_item_all():
    try:
        response = table.scan()
        items = response.get('Items')
        if items is not None and len(items) > 0:
            logging.info(f"Found {len(items)} items")
            return {"statusCode": 200, "body": json.dumps(items)}
        else:
            logging.info("No items found")
            return {"statusCode": 404, "body": json.dumps("No items found")}
    except ClientError as e:
        logging.error(f"Error getting items: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Error getting items: {e}")}
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Unexpected error: {e}")}

# Function to update an item in the table
def update_item(item_id, data):
    try:
        update_expression = "SET " + ", ".join([f"{key} = :{key}" for key in data.keys()])
        expression_attribute_values = {f":{key}": value for key, value in data.items()}

        table.update_item(
            Key={"id": item_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW",
        )
        logging.info(f"Item updated successfully: {item_id}")
        return {"statusCode": 200, "body": json.dumps("Item updated successfully")}
    except ClientError as e:
        logging.error(f"Error updating item: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Error updating item: {e}")}
# Function to delete an item from the table
def delete_item(item_id):
    try:
        table.delete_item(Key={"id": item_id})
        logging.info(f"Item deleted successfully: {item_id}")
        return {"statusCode": 200, "body": json.dumps("Item deleted successfully")}
    except ClientError as e:
        logging.error(f"Error deleting item: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Error deleting item: {e}")}

def lambda_handler(event, context):
    try:
        http_method = event.get("httpMethod")
        if http_method == "POST":
            data = json.loads(event["body"])
            return create_item(data)
        elif http_method == "GET":
            path_parameters = event.get("pathParameters")
            if path_parameters and "id" in path_parameters:
                item_id = path_parameters["id"]
                return get_item(item_id)
            else:
                return get_item_all()
        elif http_method == "PUT":
            path_parameters = event.get("pathParameters")
            if path_parameters and "id" in path_parameters:
                item_id = path_parameters["id"]
                data = json.loads(event["body"])
                return update_item(item_id, data)
            else:
                logging.error("Missing item ID in path parameters for PUT request")
                return {"statusCode": 400, "body": json.dumps("Missing item ID in path parameters")}
        elif http_method == "DELETE":
            path_parameters = event.get("pathParameters")
            if path_parameters and "id" in path_parameters:
                item_id = path_parameters["id"]
                return delete_item(item_id)
            else:
                logging.error("Missing item ID in path parameters for DELETE request")
                return {"statusCode": 400, "body": json.dumps("Missing item ID in path parameters")}
        else:
            logging.error(f"Unsupported HTTP method: {http_method}")
            return {"statusCode": 405, "body": json.dumps("Unsupported HTTP method")}
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Unexpected error: {e}")}
