import json
import os
import boto3
import logging
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def compare_objects(s3_client, source_bucket, destination_bucket, key):
    """
    Compare objects in source and destination buckets to determine if copy is needed.
    Returns True if objects are different (or destination doesn't exist), False if they're the same.
    """
    try:
        # Get source object metadata
        source_meta = s3_client.head_object(Bucket=source_bucket, Key=key)
        source_etag = source_meta['ETag']
        source_size = source_meta['ContentLength']
        
        try:
            # Try to get destination object metadata
            dest_meta = s3_client.head_object(Bucket=destination_bucket, Key=key)
            dest_etag = dest_meta['ETag']
            dest_size = dest_meta['ContentLength']
            
            # Compare ETag and size
            if source_etag == dest_etag and source_size == dest_size:
                logger.info(f"Object {key} already exists in destination with matching ETag and size")
                return False
            else:
                logger.info(f"Object {key} exists in destination but has different ETag or size")
                return True
                
        except ClientError as e:
            # If destination object doesn't exist, we need to copy
            if e.response['Error']['Code'] == '404':
                logger.info(f"Object {key} does not exist in destination bucket")
                return True
            else:
                # Re-raise other errors
                raise
                
    except Exception as e:
        logger.error(f"Error comparing {key}: {str(e)}")
        # When in doubt, copy the object
        return True

def copy_object(s3_client, source_bucket, destination_bucket, key):
    """
    Copy a single object from source to destination bucket
    """
    try:
        logger.info(f"Copying: {source_bucket}/{key} -> {destination_bucket}/{key}")
        s3_client.copy_object(
            Bucket=destination_bucket,
            CopySource={
                'Bucket': source_bucket,
                'Key': key
            },
            Key=key
        )
        return True
    except Exception as e:
        logger.error(f"Error copying {key}: {str(e)}")
        return False

def handler(event, _):
    logger.info("Event received: %s", json.dumps(event))
    
    try:
        # Parse event
        source_bucket = event.get('sourceBucket')
        destination_bucket = os.environ.get('DESTINATION_BUCKET')
        prefix = event.get('prefix', '')  # Default to empty string if not provided
        
        if not source_bucket:
            raise ValueError("Source bucket not specified in event")
        
        # Make region required
        source_region = event.get('region')
        if not source_region:
            raise ValueError("Region not specified in event")
        
        logger.info(f"Syncing from {source_bucket} to {destination_bucket} with prefix '{prefix}'")
        
        # Create S3 client
        s3_client = boto3.client('s3', region_name=source_region)
        
        # Log client region for debugging
        client_region = s3_client.meta.region_name
        logger.info(f"S3 client is using region: {client_region}")
        
        # Get all objects with the specified prefix
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=source_bucket, Prefix=prefix)
        
        total_objects = 0
        copied_objects = 0
        skipped_objects = 0
        failed_objects = 0
        
        # Process each page of results
        for page in page_iterator:
            if 'Contents' not in page:
                logger.info(f"No objects found with prefix '{prefix}'")
                continue
                
            # Process each object
            for obj in page['Contents']:
                key = obj['Key']
                total_objects += 1
                
                # Skip directories/folders (objects that end with '/')
                if key.endswith('/'):
                    logger.info(f"Skipping directory: {key}")
                    skipped_objects += 1
                    continue
                
                # Check if we need to copy this object
                if compare_objects(s3_client, source_bucket, destination_bucket, key):
                    # Objects are different, copy required
                    if copy_object(s3_client, source_bucket, destination_bucket, key):
                        copied_objects += 1
                    else:
                        failed_objects += 1
                else:
                    # Objects are the same, skip copy
                    skipped_objects += 1
        
        logger.info(f"Sync completed. Total: {total_objects}, Copied: {copied_objects}, " +
                    f"Skipped: {skipped_objects}, Failed: {failed_objects}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'S3 sync operation completed',
                'statistics': {
                    'totalObjects': total_objects,
                    'copiedObjects': copied_objects,
                    'skippedObjects': skipped_objects,
                    'failedObjects': failed_objects
                }
            })
        }
    
    except Exception as e:
        logger.error(f"Error in S3 sync operation: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error in S3 sync operation: {str(e)}')
        }