import json
import logging
import boto3
import os
from datetime import datetime, UTC

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def process_event(event):
    try:
        if event is None:
            raise ValueError("Event cannot be None")
            
        logger.info("Processing event: %s", json.dumps(event))
        
        # Get event bucket from environment variable
        event_bucket = os.environ.get('EVENT_BUCKET')
        if not event_bucket:
            raise ValueError("EVENT_BUCKET environment variable is not set")
            
        # Get event ID from the event
        event_id = event.get('id')
        if not event_id:
            raise ValueError("Event must contain an 'id' field")
            
        # Generate the datetime-based prefix
        now = datetime.now(UTC)
        prefix = f"events/{now.year:04d}/{now.month:02d}/{now.day:02d}/{event_id}"
        
        # Initialize S3 client
        s3_client = boto3.client('s3')

        # Store the event in S3
        s3_client.put_object(
            Bucket=event_bucket,
            Key=prefix,
            Body=json.dumps(event),
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'event_id': event_id,
                'location': f"s3://{event_bucket}/{prefix}"
            })
        }
    except Exception as e:
        logger.error("Error processing event: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def handler(event, context):
    logger.info("Received event: %s", json.dumps(event))
    return process_event(event) 