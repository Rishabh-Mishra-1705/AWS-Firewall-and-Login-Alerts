import json
import boto3
import gzip
import io
import uuid

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('consoleLogin')


def generate_unique_id():
    return str(uuid.uuid4())


def process_log_file(bucket, key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    compressed_content = response['Body'].read()

    # Decompress the Gzip content
    with gzip.GzipFile(fileobj=io.BytesIO(compressed_content)) as f:
        content = f.read().decode('utf-8')

    # Parse the CloudTrail log
    try:
        log_data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for {key}: {e}")
        return

    # Check if 'Records' key exists
    if 'Records' not in log_data:
        print(f"No 'Records' key in log data for {key}")
        return

    # Extract the relevant information from the log
    for record in log_data['Records']:
        event_source = record['eventSource']
        event_time = record['eventTime']
        event_name = record['eventName']
        aws_region = record['awsRegion']
        source_ip = record['sourceIPAddress']
        user_agent = record['userAgent']

        # Check if 'errorMessage' exists in the record
        error_message = record.get('errorMessage', 'None')

        # Handle login events
        if event_name == 'ConsoleLogin':
            login_status = record.get('responseElements', {}).get('ConsoleLogin', 'Unknown')
            print(login_status)
            if login_status == 'Failure':
                user_identity = record.get('userIdentity', {})
                principal_id = user_identity.get('principalId', 'Unknown')

                table.put_item(
                    Item={
                        'Id': generate_unique_id(),
                        'eventSource': event_source,
                        'eventName': event_name,
                        'eventTime': event_time,
                        'awsRegion': aws_region,
                        'sourceIPAddress': source_ip,
                        'errorMessage': error_message,
                        'userAgent': user_agent,
                        'loginStatus': login_status,
                        'username': principal_id
                    }
                )

    # Delete the object after processing
    # s3.delete_object(Bucket=bucket, Key=key)
    # print(f"Deleted {key} from bucket {bucket}")


def lambda_handler(event, context):
    # Get the S3 bucket name from the event
    bucket = event['Records'][0]['s3']['bucket']['name']

    # Define the prefix to start from the 'ap-south-1' folder
    prefix = "pci/AWSLogs/208294835209/CloudTrail/ap-south-1/2024/08/"

    s3 = boto3.client('s3')

    # Initialize pagination variables
    continuation_token = None
    while True:
        list_args = {'Bucket': bucket, 'Prefix': prefix}
        if continuation_token:
            list_args['ContinuationToken'] = continuation_token

        response = s3.list_objects_v2(**list_args)

        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                process_log_file(bucket, key)

        if response.get('IsTruncated'):  # More objects available
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    return {
        'statusCode': 200,
        'body': json.dumps('All logs processed and deleted successfully')
    }
