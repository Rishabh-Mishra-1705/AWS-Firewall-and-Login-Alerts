import json
import boto3
import gzip
import io
import uuid

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('firewall-changes')


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
        request_params = record.get('requestParameters', {})
        print(request_params)

        # Handle security group rule modification events
        if event_name == 'ModifySecurityGroupRules' and request_params:
            security_group_rule_id = request_params.get('ModifySecurityGroupRulesRequest', {}).get('SecurityGroupRule',
                                                                                                   {}).get(
                'SecurityGroupRuleId', 'Unknown')
            cidr_ipv4 = request_params.get('ModifySecurityGroupRulesRequest', {}).get('SecurityGroupRule', {}).get(
                'CidrIpv4', 'Unknown')
            from_port = request_params.get('ModifySecurityGroupRulesRequest', {}).get('SecurityGroupRule', {}).get(
                'FromPort', 'Unknown')
            to_port = request_params.get('ModifySecurityGroupRulesRequest', {}).get('SecurityGroupRule', {}).get(
                'ToPort', 'Unknown')
            ip_protocol = request_params.get('ModifySecurityGroupRulesRequest', {}).get('SecurityGroupRule', {}).get(
                'IpProtocol', 'Unknown')
            group_id = request_params.get('ModifySecurityGroupRulesRequest', {}).get('GroupId', 'Unknown')

            principal_id = record.get('userIdentity', {}).get('principalId', 'Unknown')

            table.put_item(
                Item={
                    'Id': generate_unique_id(),
                    'SecurityGroupRuleId': security_group_rule_id,
                    'eventSource': event_source,
                    'eventName': event_name,
                    'eventTime': event_time,
                    'awsRegion': aws_region,
                    'sourceIPAddress': source_ip,
                    'userAgent': user_agent,
                    'cidrIpv4': cidr_ipv4,
                    'fromPort': from_port,
                    'toPort': to_port,
                    'IpProtocol': ip_protocol,
                    'groupId': group_id,
                    'principalId': principal_id
                }
            )

    # Delete the object after processing
    s3.delete_object(Bucket=bucket, Key=key)
    print(f"Deleted {key} from bucket {bucket}")


def lambda_handler(event, context):
    # Get the S3 bucket name from the event
    bucket = event['Records'][0]['s3']['bucket']['name']

    # Define the prefix to start from the 'ap-south-1' folder
    prefix = "pci/AWSLogs/208294835209/CloudTrail/ap-south-1/2024/08/11/"

    s3 = boto3.client('s3')

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
                process_log_file(bucket, key)

        # Check if there are more objects to list
        if response.get('IsTruncated'):  # More objects available
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    return {
        'statusCode': 200,
        'body': json.dumps('All logs processed and deleted successfully')
    }
