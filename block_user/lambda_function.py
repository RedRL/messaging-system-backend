import json
import boto3
import os
from shared.dynamodb_client import get_dynamodb_table, put_item_with_retry, get_item_with_retry

dynamodb = boto3.resource('dynamodb')
blocks_table = get_dynamodb_table('Blocks')
users_table = get_dynamodb_table('Users')

def user_exists(user_id):
    response = get_item_with_retry(users_table, {'user_id': user_id})
    return 'Item' in response

def lambda_handler(event, context):
    body = json.loads(event['body'])
    user_id = body['user_id']
    blocked_user_id = body['blocked_user_id']

    if not user_exists(user_id) or not user_exists(blocked_user_id):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'User or blocked user does not exist'})
        }

    try:
        put_item_with_retry(blocks_table, {'user_id': user_id, 'blocked_user_id': blocked_user_id})
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User blocked successfully'})
        }
    except Exception as e:
        print(f"Error blocking user in DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to block user'})
        }
