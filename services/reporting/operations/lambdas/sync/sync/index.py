import json
import os
import boto3
import logging
from .object_sync import handler as object_sync_handler
from .full_sync import handler as full_sync_handler

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_object_size(s3_client, bucket, key):
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        return response['ContentLength']
    except Exception as e:
        logger.error(f"Error getting object size for {bucket}/{key}: {str(e)}")
        return None

def handler(event, context):
    """
    Main handler that routes the request to either object_sync or full_sync based on the action field.
    If action is 'full_sync', it routes to full_sync handler, otherwise it routes to object_sync handler.
    """
    logger.info("Event received: %s", json.dumps(event))
    
    # Check if this is a full sync request
    if event.get('action') == 'full_sync':
        logger.info("Routing to full sync handler")
        return full_sync_handler(event, context)
    else:
        logger.info("Routing to object sync handler")
        return object_sync_handler(event, context)