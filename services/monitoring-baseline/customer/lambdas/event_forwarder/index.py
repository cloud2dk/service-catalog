import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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

        eventbridge = boto3.client('events', region_name=event_bus_region)
        
        # Extract and validate SNS message
        try:
            sns_message = event['Records'][0]['Sns']['Message']
            logger.info("Received SNS message: %s", sns_message)
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid SNS event structure: {str(e)}")

        # Check if this is a cost anomaly message
        source = 'cloud2.services'
        detail_type = 'SNSMessage'
        
        try:
            # Parse SNS message to detect cost anomaly
            message_data = json.loads(sns_message)
            if 'anomalyId' in message_data or 'anomalyScore' in message_data:
                source = 'cloud2.ce.anomaly'
                detail_type = 'CostAnomalyDetected'
                logger.info("Detected cost anomaly message, using source: %s", source)
        except (json.JSONDecodeError, TypeError):
            # If message isn't JSON or doesn't contain anomaly fields, use default
            logger.info("Using default source for non-anomaly message")

        # Prepare the event entry
        event_entry = {
            'Source': source,
            'DetailType': detail_type,
            'Detail': sns_message,
            'EventBusName': event_bus_arn
        }
        logger.info("Prepared event entry: %s", json.dumps(event_entry))

        # Send the event to EventBridge
        response = eventbridge.put_events(Entries=[event_entry])
        
        # Check for failures
        if response.get('FailedEntryCount', 0) > 0:
            logger.error("Failed to send events: %s", json.dumps(response))
            raise Exception("Failed to send events to EventBridge")

        logger.info("Successfully sent event to EventBridge: %s", json.dumps(response))
        return {
            'statusCode': 200,
            'body': 'Event sent to EventBridge successfully!'
        }

    except Exception as e:
        logger.error("Error processing event: %s", str(e))
        raise