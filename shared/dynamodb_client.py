import boto3
from botocore.config import Config
from retry import retry

# Configure retry strategy
retry_config = Config(
    retries={
        'max_attempts': 10,  # Maximum number of retry attempts
        'mode': 'standard'   # Retry mode
    }
)

# Create DynamoDB resource with retry configuration
dynamodb = boto3.resource('dynamodb', config=retry_config)

def get_dynamodb_table(table_name):
    return dynamodb.Table(table_name)

@retry(tries=5, delay=2, backoff=2)
def put_item_with_retry(table, item):
    table.put_item(Item=item)

@retry(tries=5, delay=2, backoff=2)
def get_item_with_retry(table, key):
    return table.get_item(Key=key)

@retry(tries=5, delay=2, backoff=2)
def batch_get_items_with_retry(table, keys):
    request_items = {table.name: {'Keys': keys}}
    response = table.meta.client.batch_get_item(RequestItems=request_items)
    return response

@retry(tries=5, delay=2, backoff=2)
def update_item_with_retry(table, key, update_expression, expression_attribute_values, expression_attribute_names=None):
    update_kwargs = {
        'Key': key,
        'UpdateExpression': update_expression,
        'ExpressionAttributeValues': expression_attribute_values
    }
    if expression_attribute_names:
        update_kwargs['ExpressionAttributeNames'] = expression_attribute_names

    table.update_item(**update_kwargs)

