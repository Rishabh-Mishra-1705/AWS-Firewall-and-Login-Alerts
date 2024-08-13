## Firewall Changes and Console Login Alerts - Ticket Generation
Overview
This project involves the automation of ticket generation for firewall changes and console login alerts. The solution is built using AWS services such as Lambda, DynamoDB, and S3. The primary goal is to monitor AWS CloudTrail logs for specific events, process the logs, and automatically generate tickets when firewall changes or console login failures are detected.

Project Structure
The project consists of several components, each responsible for different parts of the overall solution:

CloudTrail Log Parser (cloudtrailparser): This Lambda function processes CloudTrail logs stored in an S3 bucket. It identifies specific events such as security group changes or console login attempts and transfers the corresponding logs to dedicated S3 buckets for further processing.

Firewall Changes Parser (firewall_changes_parser): This Lambda function processes the logs related to firewall changes (specifically, security group rule modifications). The parsed information is then stored in a DynamoDB table, and the log file is deleted from S3 after processing.

Console Login Parser (consolelogin_parser): This Lambda function handles logs related to console login attempts. If a login attempt fails, the relevant details are extracted and stored in a DynamoDB table.

Firewall Alert Ticket Generation (firewall_alert_parser): This Lambda function is triggered by insert events in the DynamoDB table. It logs into a ticketing system, extracts the necessary details from the new record, and generates a ticket for non-compliance firewall changes.

Components
CloudTrail Log Parser (cloudtrailparser)
Purpose: Process CloudTrail logs stored in S3 and transfer logs with specific events (ModifySecurityGroupRules, ConsoleLogin) to separate S3 buckets for further processing.
Trigger: S3 Event notifications.
Processing:
Decompresses and reads the log files.
Checks for the presence of specific event names.
Transfers the log to the appropriate S3 bucket based on the event type.
Key Functions:
process_log_file: Processes each log file and identifies the event type.
transfer_to_bucket: Transfers the log to the target S3 bucket.
Firewall Changes Parser (firewall_changes_parser)
Purpose: Process security group rule modification logs and store relevant details in a DynamoDB table.
Trigger: S3 Event notifications.
Processing:
Decompresses and reads the log files.
Extracts relevant information (such as SecurityGroupRuleId, CidrIpv4, FromPort, ToPort, etc.) from the logs.
Stores the extracted information in the DynamoDB table (firewall-changes).
Deletes the log file from S3 after processing.
Key Functions:
process_log_file: Processes each log file, extracts details, and inserts them into DynamoDB.
generate_unique_id: Generates a unique ID for each record in DynamoDB.
Console Login Parser (consolelogin_parser)
Purpose: Process console login attempt logs, and store failed login attempts in a DynamoDB table.
Trigger: S3 Event notifications.
Processing:
Decompresses and reads the log files.
Checks for failed console login attempts.
Extracts relevant information (such as sourceIPAddress, eventName, userAgent, etc.) and stores it in the DynamoDB table (consoleLogin).
Key Functions:
process_log_file: Processes each log file, identifies failed login attempts, and inserts them into DynamoDB.
generate_unique_id: Generates a unique ID for each record in DynamoDB.
Firewall Alert Ticket Generation (firewall_alert_parser)
Purpose: Generate tickets for firewall changes detected by the firewall_changes_parser.
Trigger: DynamoDB Stream on INSERT events in the firewall-changes table.
Processing:
Logs into the ticketing system to obtain an authorization token.
Extracts information from the new record in DynamoDB.
Generates a ticket in the ticketing system with the extracted information.
Key Functions:
tic_login: Authenticates with the ticketing system and retrieves a bearer token.
genticket: Generates a ticket with the provided details.
Deployment
AWS Lambda: Deploy the provided Lambda functions for processing CloudTrail logs, generating tickets, and storing relevant information in DynamoDB.
DynamoDB: Ensure the DynamoDB tables (firewall-changes, consoleLogin) are set up with the appropriate schema.
S3 Buckets: Configure the S3 buckets to store CloudTrail logs and the processed logs.
Triggers: Set up triggers for the Lambda functions:
S3 Event notifications for log processing.
DynamoDB Streams for ticket generation.
Usage
Ensure that CloudTrail is configured to deliver logs to the designated S3 bucket.
The cloudtrailparser function will process incoming logs and route them to appropriate buckets.
The firewall_changes_parser and consolelogin_parser will process logs and store necessary details in DynamoDB.
The firewall_alert_parser will generate tickets based on the events captured in DynamoDB.
Contributing
Feel free to submit issues, fork the repository, and send pull requests. 
Contributions are welcome!
