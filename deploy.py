import boto3
import uuid
import os
import subprocess
import zipfile

REGION = 'eu-north-1'

def create_bucket(bucket_name, region):
    s3_client = boto3.client('s3', region_name=region)
    try:
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
        print(f'S3 bucket created: {bucket_name}')
    except Exception as e:
        print(f'Failed to create bucket: {e}')
        raise

def generate_unique_bucket_name(prefix):
    bucket_name = f'{prefix}-{uuid.uuid4()}'
    bucket_name = bucket_name[:42]
    return bucket_name

def zip_lambda_function(source_dir, output_filename, dependencies_dir):
    with zipfile.ZipFile(output_filename, 'w') as zf:
        # Add function code
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=source_dir)
                zf.write(file_path, arcname)
        # Add shared directory
        shared_dir = 'shared'
        for root, _, files in os.walk(shared_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start='.')
                zf.write(file_path, arcname)
        # Add dependencies
        for root, _, files in os.walk(dependencies_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=dependencies_dir)
                zf.write(file_path, arcname)

def install_dependencies(target_dir):
    subprocess.check_call([
        'pip', 'install', '--upgrade', 'retry', '--target', target_dir
    ])

def upload_to_s3(file_name, bucket, object_name=None):
    s3_client = boto3.client('s3')
    if object_name is None:
        object_name = file_name
    try:
        s3_client.upload_file(file_name, bucket, object_name)
        print(f'Uploaded {file_name} to bucket {bucket}')
    except Exception as e:
        print(f'Failed to upload {file_name} to bucket {bucket}: {e}')
        raise

def deploy_cloudformation_stack(template_file, stack_name, bucket_name, lambda_zips):
    cloudformation_client = boto3.client('cloudformation', region_name=REGION)
    with open(template_file, 'r') as file:
        template_body = file.read()
    parameters = [
        {'ParameterKey': 'BucketName', 'ParameterValue': bucket_name}
    ]
    for key, value in lambda_zips.items():
        parameters.append({'ParameterKey': key, 'ParameterValue': value})
    try:
        response = cloudformation_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=parameters,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND']
        )
        print('Stack creation initiated')
    except cloudformation_client.exceptions.AlreadyExistsException:
        response = cloudformation_client.update_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=parameters,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND']
        )
        print('Stack update initiated')
    except Exception as e:
        print(f'Failed to create or update stack: {e}')
        raise
    return response

def main():
    # Generate a unique bucket name
    bucket_name = generate_unique_bucket_name('messaging-system-lambda-functions')

    # Create S3 bucket if it doesn't exist
    create_bucket(bucket_name, REGION)

    # List of Lambda function directories and ZIP filenames
    lambda_functions = {
        'RegisterUserFunction': 'register_user',
        'SendMessageFunction': 'send_message',
        'ProcessUserMessageFunction': 'process_user_message',
        'SendGroupMessageFunction': 'send_group_message',
        'ProcessGroupMessageFunction': 'process_group_message',
        'BlockUserFunction': 'block_user',
        'CreateGroupFunction': 'create_group',
        'AddUserToGroupFunction': 'add_user_to_group',
        'RemoveUserFromGroupFunction': 'remove_user_from_group',
        'GetAllMessagesFunction': 'get_all_messages',
        'GetNewMessagesFunction': 'get_new_messages'
    }

    # Install dependencies for shared module
    install_dependencies('shared/dependencies/python')

    lambda_zips = {}
    for function_name, directory in lambda_functions.items():
        zip_filename = f'{directory}.zip'
        zip_lambda_function(directory, zip_filename, 'shared/dependencies/python')
        upload_to_s3(zip_filename, bucket_name)
        lambda_zips[f'{function_name}ZipKey'] = zip_filename

    # Deploy CloudFormation stack
    deploy_cloudformation_stack('template.yaml', 'MessagingSystemStack', bucket_name, lambda_zips)
    print('Deployment complete')

if __name__ == "__main__":
    main()
