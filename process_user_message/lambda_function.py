import json
import boto3
import uuid
from datetime import datetime
from shared.dynamodb_client import get_dynamodb_table, get_item_with_retry, put_item_with_retry, update_item_with_retry

dynamodb = boto3.resource('dynamodb')
messages_table = get_dynamodb_table('Messages')
users_table = get_dynamodb_table('Users')
blocks_table = get_dynamodb_table('Blocks')

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        sender_id = body['sender_id']
        receiver_id = body['receiver_id']
        message = body['message']

        # Check if sender is blocked by receiver
        response = get_item_with_retry(blocks_table, {'user_id': receiver_id})
        if 'Item' in response and sender_id in response['Item'].get('blocked_users', []):
            continue

        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        message_item = {
            'message_id': message_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': message,
            'timestamp': timestamp,
            'is_read': False
        }

        try:
            # Put message in Messages table
            put_item_with_retry(messages_table, message_item)

            # Add message ID to receiver's received messages in Users table
            update_item_with_retry(users_table, {'user_id': receiver_id},
                                   'SET received_messages = list_append(if_not_exists(received_messages, :empty_list), :new_message_id)',
                                   {':new_message_id': [message_id], ':empty_list': []})

        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to process message'})
            }

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'success'})
    }
