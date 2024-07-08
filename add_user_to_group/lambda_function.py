import json
from shared.dynamodb_client import get_dynamodb_table, get_item_with_retry, update_item_with_retry

users_table = get_dynamodb_table('Users')
groups_table = get_dynamodb_table('Groups')

def user_exists(user_id):
    response = get_item_with_retry(users_table, {'user_id': user_id})
    return 'Item' in response

def lambda_handler(event, context):
    body = json.loads(event['body'])
    group_id = body['group_id']
    user_id = body['user_id']
    
    # Check if user exists
    if not user_exists(user_id):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'User with ID {user_id} does not exist'})
        }

    # Check if group exists and get its members
    group_response = get_item_with_retry(groups_table, {'group_id': group_id})
    if 'Item' not in group_response:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Group with ID {group_id} does not exist'})
        }
    
    members = group_response['Item'].get('members', [])

    # Prevent adding user multiple times
    if user_id in members:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'User with ID {user_id} is already a member of the group'})
        }

    # Add user to group
    try:
        update_item_with_retry(groups_table, {'group_id': group_id},
                               'SET members = list_append(if_not_exists(members, :empty_list), :new_member)',
                               {':new_member': [user_id], ':empty_list': []})
    except Exception as e:
        print(f"Error updating item in DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to add user to group'})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'User added to group successfully'})
    }
