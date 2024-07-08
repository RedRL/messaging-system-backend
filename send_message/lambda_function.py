import json
import boto3
import os
from shared.dynamodb_client import get_dynamodb_table, get_item_with_retry

dynamodb = boto3.resource('dynamodb')
users_table = get_dynamodb_table('Users')
blocks_table = get_dynamodb_table('Blocks')
sqs = boto3.client('sqs')
queue_url = os.environ['QUEUE_URL']

def user_exists(user_id):
    response = get_item_with_retry(users_table, {'user_id': user_id})
    return 'Item' in response

def is_blocked(sender_id, receiver_id):
    response = blocks_table.query(
        IndexName='BlockedUserIndex',
        KeyConditionExpression='blocked_user_id = :blocked_user_id AND user_id = :user_id',
        ExpressionAttributeValues={
            ':blocked_user_id': sender_id,
            ':user_id': receiver_id
        }
    )
    return response['Count'] > 0

def lambda_handler(event, context):
    body = json.loads(event['body'])
    sender_id = body['sender_id']
    receiver_id = body['receiver_id']
    message = body['message']

    if not user_exists(sender_id) or not user_exists(receiver_id):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Sender or receiver does not exist'})
        }

    if is_blocked(sender_id, receiver_id):
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'You are blocked by the receiver'})
        }

    # If both exist and the sender is not blocked, send message to SQS
    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                'sender_id': sender_id,
                'receiver_id': receiver_id,
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
