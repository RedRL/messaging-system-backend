import json
import boto3
import os
from shared.dynamodb_client import get_dynamodb_table, update_item_with_retry

dynamodb = boto3.resource('dynamodb')
groups_table = dynamodb.Table('Groups')

def lambda_handler(event, context):
    body = json.loads(event['body'])
    group_id = body['group_id']
    user_id = body['user_id']

    try:
        response = groups_table.get_item(
            Key={'group_id': group_id}
        )
    except Exception as e:
        print(f"Error getting group from DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to get group'})
        }

    if 'Item' not in response:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Group not found'})
        }

    members = response['Item'].get('members', [])
    if user_id not in members:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'User not in group'})
        }

    members.remove(user_id)

    try:
        update_item_with_retry(groups_table,
            {'group_id': group_id},
            'SET members = :members',
            {':members': members}
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User removed from group successfully'})
        }
    except Exception as e:
        print(f"Error updating group in DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to update group'})
        }
