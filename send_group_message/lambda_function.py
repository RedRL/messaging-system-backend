import json
import boto3
import uuid
import os
from shared.dynamodb_client import get_dynamodb_table, get_item_with_retry, put_item_with_retry

dynamodb = boto3.resource('dynamodb')
users_table = get_dynamodb_table('Users')
groups_table = get_dynamodb_table('Groups')
sqs = boto3.client('sqs')
queue_url = os.getenv('QUEUE_URL')

def user_exists(user_id):
    response = get_item_with_retry(users_table, {'user_id': user_id})
    return 'Item' in response

def lambda_handler(event, context):
    body = json.loads(event['body'])
    sender_id = body['sender_id']
    group_id = body['group_id']
    message = body['message']
    
    # Check if sender exists
    if not user_exists(sender_id):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Sender with ID {sender_id} does not exist'})
        }
    
    try:
        response = get_item_with_retry(groups_table, {'group_id': group_id})
    except Exception as e:
        print(f"Error getting item from DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to retrieve group'})
        }

    if 'Item' not in response:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Group with ID {group_id} does not exist'})
        }
    
    members = response['Item'].get('members', [])

    # Check if sender is a member of the group
    if sender_id not in members:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'User is not a member of the group'})
        }

    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                'sender_id': sender_id,
                'group_id': group_id,
                'message': message
            })
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message_id': response['MessageId']})
        }
    except Exception as e:
        print(f"Error sending message to SQS: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to send message'})
        }
