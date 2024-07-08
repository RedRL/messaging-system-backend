import json
import boto3
import uuid
from datetime import datetime
from shared.dynamodb_client import get_dynamodb_table, get_item_with_retry, put_item_with_retry, update_item_with_retry

dynamodb = boto3.resource('dynamodb')
groups_table = get_dynamodb_table('Groups')
users_table = get_dynamodb_table('Users')
messages_table = get_dynamodb_table('Messages')

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        sender_id = body['sender_id']
        group_id = body['group_id']
        message = body['message']

        try:
            response = get_item_with_retry(groups_table, {'group_id': group_id})
        except Exception as e:
            continue

        if 'Item' in response:
            members = response['Item'].get('members', [])
            if sender_id in members:
                message_id = str(uuid.uuid4())
                timestamp = datetime.utcnow().isoformat()
                message_item = {
                    'message_id': message_id,
                    'sender_id': sender_id,
                    'message': message,
                    'group_id': group_id,
                    'timestamp': timestamp,
                    'is_read': {member: False for member in members}
                }

                try:
                    # Put message in Messages table
                    put_item_with_retry(messages_table, message_item)
                except Exception as e:
                    continue

                for member in members:
                    try:
                        # Add message ID to member's received messages in Users table
                        update_item_with_retry(users_table, {'user_id': member},
                                               'SET received_messages = list_append(if_not_exists(received_messages, :empty_list), :new_message_id)',
                                               {':new_message_id': [message_id], ':empty_list': []})
                    except Exception as e:
                        continue

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'success'})
    }
