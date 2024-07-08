import json
import uuid
from shared.dynamodb_client import get_dynamodb_table, put_item_with_retry

users_table = get_dynamodb_table('Users')

def lambda_handler(event, context):
    user_id = str(uuid.uuid4())
    try:
        # Use the retry logic for putting an item
        put_item_with_retry(users_table, {'user_id': user_id})
    except Exception as e:
        print(f"Error putting item in DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to register user'})
        }
    return {
        'statusCode': 200,
        'body': json.dumps({'user_id': user_id})
    }
