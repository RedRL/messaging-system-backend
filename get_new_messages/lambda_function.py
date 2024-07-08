import json
from shared.dynamodb_client import get_dynamodb_table, batch_get_items_with_retry, get_item_with_retry, update_item_with_retry

users_table = get_dynamodb_table('Users')
messages_table = get_dynamodb_table('Messages')

def lambda_handler(event, context):
    try:
        if 'queryStringParameters' not in event or event['queryStringParameters'] is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing query string parameters'})
            }

        user_id = event['queryStringParameters'].get('user_id')
        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing user_id in query string parameters'})
            }

        user_response = get_item_with_retry(users_table, {'user_id': user_id})
        if 'Item' not in user_response:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'User with ID {user_id} does not exist'})
            }

        message_ids = user_response['Item'].get('received_messages', [])
        if not message_ids:
            return {
                'statusCode': 200,
                'body': json.dumps({'messages': []})
            }

        message_keys = [{'message_id': message_id} for message_id in message_ids]
        response = batch_get_items_with_retry(messages_table, message_keys)
        messages = response.get('Responses', {}).get('Messages', [])

        formatted_messages = []
        for message in messages:
            is_read = message['is_read']
            if isinstance(is_read, bool):
                # Handle individual messages
                if not is_read:
                    formatted_message = {
                        'message': message['message'],
                        'sender_id': message['sender_id'],
                        'timestamp': message['timestamp']
                    }
                    if 'group_id' in message:
                        formatted_message['received_from'] = message['sender_id']
                        formatted_message['group_id'] = message['group_id']
                    formatted_messages.append(formatted_message)

                    # Mark the message as read for this user
                    update_item_with_retry(
                        messages_table, 
                        {'message_id': message['message_id']},
                        'SET is_read = :true',
                        {':true': True}
                    )
            elif isinstance(is_read, dict):
                # Handle group messages
                if not is_read.get(user_id, False):
                    formatted_message = {
                        'message': message['message'],
                        'sender_id': message['sender_id'],
                        'timestamp': message['timestamp']
                    }
                    if 'group_id' in message:
                        formatted_message['received_from'] = message['sender_id']
                        formatted_message['group_id'] = message['group_id']
                    formatted_messages.append(formatted_message)

                    # Mark the message as read for this user
                    update_expression = f"SET is_read.#user_id = :true"
                    update_item_with_retry(
                        messages_table, 
                        {'message_id': message['message_id']},
                        update_expression,
                        {':true': True},
                        expression_attribute_names={'#user_id': user_id}
                    )

        # Sort messages by timestamp (oldest first)
        formatted_messages.sort(key=lambda x: x['timestamp'])

        return {
            'statusCode': 200,
            'body': json.dumps({'messages': formatted_messages})
        }

    except Exception as e:
        print(f"Error retrieving new messages: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to retrieve new messages'})
        }
