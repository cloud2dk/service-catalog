import boto3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to simulate call-home events for testing monitoring pipeline.
    Sends events to EventBridge, SNS, and CloudWatch.
    """
    logger.info("Call-home Lambda triggered with event: %s", json.dumps(event))

    try:
        # Get configuration from environment variables
        operations_account_id = os.getenv('OPERATIONS_ACCOUNT_ID')
        event_bus_arn = os.getenv('EVENT_BUS_ARN')
        sns_topic_arn = os.getenv('SNS_TOPIC_ARN')

        if not operations_account_id:
            raise ValueError("OPERATIONS_ACCOUNT_ID environment variable is not set")
        if not event_bus_arn:
            raise ValueError("EVENT_BUS_ARN environment variable is not set")
        if not sns_topic_arn:
            raise ValueError("SNS_TOPIC_ARN environment variable is not set")

        # Extract region from EventBridge ARN
        event_bus_region = event_bus_arn.split(":")[3]

        # Initialize AWS clients
        eventbridge = boto3.client('events', region_name=event_bus_region)
        sns = boto3.client('sns')

        # Extract optional parameters from event or use defaults
        status = event.get('status', 'success')
        origin = event.get('origin', 'lambda')
        cause = event.get('cause', 'call-home-test')
        timestamp = datetime.utcnow().isoformat() + 'Z'

        # Prepare call-home payload
        call_home_payload = {
            "status": status,
            "origin": origin,
            "cause": cause,
            "timestamp": timestamp,
            "lambda_request_id": context.aws_request_id if context else "test-request-id"
        }

        logger.info("Sending call-home payload: %s", json.dumps(call_home_payload))

        # 1. Send EventBridge event to operations account
        logger.info("Sending EventBridge event to: %s", event_bus_arn)
        eventbridge_response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'cloud2.callhome.lambda',
                    'DetailType': 'CallHomeEvent',
                    'Detail': json.dumps(call_home_payload),
                    'EventBusName': event_bus_arn
                }
            ]
        )

        if eventbridge_response.get('FailedEntryCount', 0) > 0:
            logger.error("Failed to send EventBridge event: %s", json.dumps(eventbridge_response))
            raise Exception("Failed to send EventBridge event")

        logger.info("Successfully sent EventBridge event: %s", json.dumps(eventbridge_response))

        # 2. Send SNS message to local topic
        logger.info("Sending SNS message to: %s", sns_topic_arn)
        sns_response = sns.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(call_home_payload),
            Subject=f'Call Home Event - {status.upper()}'
        )

        logger.info("Successfully sent SNS message: %s", json.dumps(sns_response))

        # Return successful response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Call-home events sent successfully',
                'payload': call_home_payload,
                'responses': {
                    'eventbridge': eventbridge_response,
                    'sns': sns_response
                }
            })
        }

        logger.info("Call-home Lambda completed successfully")
        return response

    except Exception as e:
        logger.error("Error in call-home Lambda: %s", str(e))

        # Return error response
        error_response = {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Call-home Lambda failed'
            })
        }

        return error_response