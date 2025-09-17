import json
import os
import boto3
import logging

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

def handler(event, _):
    logger.info("Event received: %s", json.dumps(event))
    logger.info("Destination bucket: %s", os.environ.get('DESTINATION_BUCKET'))
    
    try:
        # Get the message from SQS message
        body = json.loads(event['Records'][0]['body'])
        logger.info("SQS message body: %s", json.dumps(body))
        
        message = json.loads(body['Message'])
        logger.info("Parsed message: %s", json.dumps(message))

        region = message['region']
        s3_client = boto3.client('s3', region_name=region)
        source_bucket = message['detail']['bucket']['name']
        source_key = message['detail']['object']['key']
        destination_bucket = os.environ.get('DESTINATION_BUCKET')
        
        logger.info(f"Source: {source_bucket}/{source_key}")
        logger.info(f"Destination: {destination_bucket}/{source_key}")

        # Get source object size
        source_size = get_object_size(s3_client, source_bucket, source_key)
        if source_size is not None:
            logger.info(f"Source object size: {source_size} bytes")
        
        # Perform the copy operation
        s3_client.copy_object(
            Bucket=destination_bucket,
            CopySource={
                'Bucket': source_bucket,
                'Key': source_key
            },
            Key=source_key
        )
        
        # Verify the copy by checking the destination object size
        dest_size = get_object_size(s3_client, destination_bucket, source_key)
        if dest_size is not None:
            logger.info(f"Destination object size: {dest_size} bytes")
            
            if source_size == dest_size:
                logger.info("Copy operation successful: Source and destination sizes match")
            else:
                logger.warning("Copy operation might have issues: Source and destination sizes do not match")
        
        return {
            'statusCode': 200,
            'body': json.dumps('S3 copy operation completed successfully')
        }
    
    except Exception as e:
        logger.error(f"Error in S3 copy operation: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error in S3 copy operation: {str(e)}')
        }