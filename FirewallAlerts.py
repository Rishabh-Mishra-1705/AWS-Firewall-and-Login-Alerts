import json
import http.client


def tic_login():
    conn = http.client.HTTPSConnection("tippi.linuxmantra.com")
    payload = json.dumps({
        "userEmail": "vishesh@ezswype.in",
        "userPwd": "Pulsar-123#"
    })
    headers = {
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/auth/login", payload, headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    return data


def genticket(ticketSource, entityCode, projectCode, ticketCategory, ticketSummary, ticketDescription, bearer_token):
    conn = http.client.HTTPSConnection("tippi.linuxmantra.com")
    payload = json.dumps({
        "ticketSource": ticketSource,
        "entity": {
            "entityCode": entityCode
        },
        "project": {
            "projectCode": projectCode
        },
        "ticketCategory": {
            "name": ticketCategory
        },
        "ticketInfo": {
            "ticketSummary": ticketSummary,
            "ticketDescription": ticketDescription
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': bearer_token
    }
    print(payload)
    conn.request("POST", "/api/tickets", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


def lambda_handler(event, context):
    logindata = tic_login()
    print(logindata)
    data = json.loads(logindata)

    bearer_token = data.get('token')

    print(bearer_token)

    entity_info = data['entities'][0]
    entity_name = entity_info.get('entityName')
    print(entity_name)
    entity_code = entity_info.get('entityCode')
    print(entity_code)
    project_info = data['projects'][0]
    project_code = project_info.get('projectCode')
    print(project_code)

    ticketCategory = "Cloud Alerts"

    # Step 2: Iterate over the records in the event to detect INSERT events
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            print("Insert event detected:", record)

            # Extract relevant information from the DynamoDB event's NewImage
            new_image = record['dynamodb'].get('NewImage', {})
            ticketDescription = {
                "Id": new_image.get('Id', {}).get('S', ''),
                "awsRegion": new_image.get('awsRegion', {}).get('S', ''),
                "cidrIpv4": new_image.get('cidrIpv4', {}).get('S', ''),
                "eventName": new_image.get('eventName', {}).get('S', ''),
                "eventSource": new_image.get('eventSource', {}).get('S', ''),
                "eventTime": new_image.get('eventTime', {}).get('S', ''),
                "fromPort": new_image.get('fromPort', {}).get('N', ''),
                "groupId": new_image.get('groupId', {}).get('S', ''),
                "IpProtocol": new_image.get('IpProtocol', {}).get('S', ''),
                "principalId": new_image.get('principalId', {}).get('S', ''),
                "SecurityGroupRuleId": new_image.get('SecurityGroupRuleId', {}).get('S', ''),
                "sourceIPAddress": new_image.get('sourceIPAddress', {}).get('S', ''),
                "toPort": new_image.get('toPort', {}).get('N', ''),
                "userAgent": new_image.get('userAgent', {}).get('S', '')
            }

            # Convert ticketDescription to a JSON string
            ticketDescriptionStr = json.dumps(ticketDescription, indent=2)
            ticketSummary = "Non Compliance: Firewall changes"
            print(f"ticket description: {ticketDescriptionStr}")

            # Step 3: Call genticket to generate a ticket using the extracted information
            # genticket(entity_name, entity_code, project_code, ticketCategory, ticketSummary, ticketDescriptionStr, bearer_token)

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda function executed successfully!')
    }
