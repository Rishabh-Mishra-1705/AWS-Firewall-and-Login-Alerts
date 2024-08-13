import boto3
import gzip
import io
import json

# Initialize the S3 client
s3 = boto3.client('s3')


def transfer_to_bucket(source_bucket, source_key, target_bucket):
    copy_source = {'Bucket': source_bucket, 'Key': source_key}
    s3.copy_object(CopySource=copy_source, Bucket=target_bucket, Key=source_key)
    print(f"Transferred {source_key} from {source_bucket} to {target_bucket}")


def process_log_file(bucket, key, target_bucket_security_group, target_bucket_console_login):
    response = s3.get_object(Bucket=bucket, Key=key)
    compressed_content = response['Body'].read()

    # Decompress the Gzip content
    with gzip.GzipFile(fileobj=io.BytesIO(compressed_content)) as f:
        content = f.read().decode('utf-8')

    # Check if the content contains the specified event names and transfer accordingly
    if '"eventName":"ModifySecurityGroupRules"' in content:
        transfer_to_bucket(bucket, key, target_bucket_security_group)
    elif '"eventName":"ConsoleLogin"' in content:
        transfer_to_bucket(bucket, key, target_bucket_console_login)


def lambda_handler(event, context):
    # Get the S3 bucket name from the event
    bucket = event['Records'][0]['s3']['bucket']['name']

    # Define the prefix to start from the 'ap-south-1' folder
    prefix = "pci/AWSLogs/208294835209/CloudTrail/ap-south-1/2024/08/"

    # Define target buckets for each event type
    target_bucket_security_group = 'securitygroup-changes'  # Replace with the target bucket for security group logs
    target_bucket_console_login = 'ezswypeconsolelogin'  # Replace with the target bucket for console login logs

    # Initialize pagination variables
    continuation_token = None
    while True:
        # List objects in the S3 bucket starting from the 'ap-south-1' folder
        list_args = {'Bucket': bucket, 'Prefix': prefix}
        if continuation_token:
            list_args['ContinuationToken'] = continuation_token

        response = s3.list_objects_v2(**list_args)

        # Process each object
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                process_log_file(bucket, key, target_bucket_security_group, target_bucket_console_login)

        # Check if there are more objects to list
        if response.get('IsTruncated'):  # More objects available
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    return {
        'statusCode': 200,
        'body': json.dumps('All logs processed successfully')
    }
