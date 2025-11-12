import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract_sns_message(event):
    try:
        return event['Records'][0]['Sns']['Message']
    except (KeyError, IndexError) as e:
        raise ValueError(f"Invalid SNS event structure: {str(e)}")


def prepare_eventbridge_detail(sns_message):
    try:
        # Try to parse as JSON (validates it's already valid JSON)
        json.loads(sns_message)
        return sns_message
    except (json.JSONDecodeError, TypeError):
        # Wrap non-JSON messages in a JSON object
        logger.info("Wrapped non-JSON message in object for EventBridge compatibility")
        return json.dumps({'message': sns_message})


def create_eventbridge_entry(detail, event_bus_arn):
    return {
        'Source': 'cloud2.events',
        'DetailType': 'SNSMessage',
        'Detail': detail,
        'EventBusName': event_bus_arn
    }


def send_to_eventbridge(eventbridge_client, event_entry):
    response = eventbridge_client.put_events(Entries=[event_entry])

    if response.get('FailedEntryCount', 0) > 0:
        logger.error("Failed to send events: %s", json.dumps(response))
        raise Exception("Failed to send events to EventBridge")

    logger.info("Successfully sent event to EventBridge: %s", json.dumps(response))


def handler(event, context):
    try:
        logger.info("Received event: %s", json.dumps(event))

        # Get and validate the Event Bus ARN
        event_bus_arn = os.getenv('EVENT_BUS_ARN')
        if not event_bus_arn:
            raise ValueError("EVENT_BUS_ARN environment variable is not set")

        # Extract region from ARN for the client
        event_bus_region = event_bus_arn.split(":")[3]
        logger.info("Using event bus ARN: %s in region: %s", event_bus_arn, event_bus_region)

        # Extract and validate SNS message
        sns_message = extract_sns_message(event)
        logger.info("Received SNS message for forwarding")

        # Prepare EventBridge event entry
        detail = prepare_eventbridge_detail(sns_message)
        event_entry = create_eventbridge_entry(detail, event_bus_arn)
        logger.info("Forwarding message to EventBridge")

        # Send to EventBridge
        eventbridge = boto3.client('events', region_name=event_bus_region)
        send_to_eventbridge(eventbridge, event_entry)

        return {
            'statusCode': 200,
            'body': 'Event sent to EventBridge successfully!'
        }

    except Exception as e:
        logger.error("Error processing event: %s", str(e))
        raise