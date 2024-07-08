import json
import uuid
from shared.dynamodb_client import get_dynamodb_table, put_item_with_retry, get_item_with_retry

users_table = get_dynamodb_table('Users')
groups_table = get_dynamodb_table('Groups')

def user_exists(user_id):
    response = get_item_with_retry(users_table, {'user_id': user_id})
    return 'Item' in response

def lambda_handler(event, context):
    body = json.loads(event['body'])
    group_id = str(uuid.uuid4())
    group_name = body['group_name']
    creator_id = body['creator_id']
    members = body.get('members', [])
    
    # Check if creator exists
    if not user_exists(creator_id):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Creator with ID {creator_id} does not exist'})
        }
    
    # Add creator to members and remove duplicates
    members = list(set(members + [creator_id]))
    
    # Check if all members exist
    for member in members:
        if not user_exists(member):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Member with ID {member} does not exist'})
            }

    try:
        # Use the retry logic for putting an item
        put_item_with_retry(groups_table, {
            'group_id': group_id,
            'group_name': group_name,
            'creator_id': creator_id,
            'members': members
        })
    except Exception as e:
        print(f"Error putting item in DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to create group'})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({'group_id': group_id})
    }
