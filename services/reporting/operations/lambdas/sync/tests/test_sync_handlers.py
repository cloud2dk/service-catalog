import json
import pytest
from unittest.mock import patch, MagicMock
from sync.index import handler
from sync.object_sync import handler as object_sync_handler
from sync.full_sync import handler as full_sync_handler

# Mock S3 event for object sync
MOCK_OBJECT_SYNC_EVENT = {
    'Records': [{
        'body': json.dumps({
            'Message': json.dumps({
                'region': 'us-east-1',
                'detail': {
                    'bucket': {
                        'name': 'source-bucket'
                    },
                    'object': {
                        'key': 'test/file.txt'
                    }
                }
            })
        })
    }]
}

# Mock S3 event for full sync
MOCK_FULL_SYNC_EVENT = {
    'action': 'full_sync',
    'sourceBucket': 'source-bucket',
    'region': 'us-east-1',
    'prefix': 'test/'
}

@pytest.fixture
def mock_s3_client():
    with patch('boto3.client') as mock_client:
        # Configure the mock client
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        
        # Mock head_object responses
        def head_object_side_effect(**kwargs):
            if kwargs.get('Bucket') == 'source-bucket':
                return {
                    'ETag': '"123456789"',
                    'ContentLength': 1000
                }
            else:  # destination bucket
                return {
                    'ETag': '"987654321"',  # Different ETag to force copy
                    'ContentLength': 1000
                }
        
        mock_s3.head_object.side_effect = head_object_side_effect
        
        # Mock copy_object
        mock_s3.copy_object.return_value = {}
        
        # Mock list_objects_v2 for full sync
        mock_s3.get_paginator.return_value.paginate.return_value = [{
            'Contents': [
                {'Key': 'test/file1.txt'},
                {'Key': 'test/file2.txt'}
            ]
        }]
        
        yield mock_s3

def test_object_sync_handler(mock_s3_client):
    """Test the object sync handler with a mock S3 event"""
    with patch.dict('os.environ', {'DESTINATION_BUCKET': 'dest-bucket'}):
        response = object_sync_handler(MOCK_OBJECT_SYNC_EVENT, None)
        
        assert response['statusCode'] == 200
        assert 'S3 copy operation completed successfully' in response['body']
        
        # Verify S3 client was called correctly
        mock_s3_client.copy_object.assert_called_once()
        call_args = mock_s3_client.copy_object.call_args[1]
        assert call_args['Bucket'] == 'dest-bucket'
        assert call_args['Key'] == 'test/file.txt'
        assert call_args['CopySource']['Bucket'] == 'source-bucket'
        assert call_args['CopySource']['Key'] == 'test/file.txt'

def test_full_sync_handler(mock_s3_client):
    """Test the full sync handler with a mock S3 event"""
    with patch.dict('os.environ', {'DESTINATION_BUCKET': 'dest-bucket'}):
        response = full_sync_handler(MOCK_FULL_SYNC_EVENT, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'statistics' in body
        stats = body['statistics']
        assert stats['totalObjects'] == 2
        assert stats['copiedObjects'] == 2
        assert stats['skippedObjects'] == 0
        assert stats['failedObjects'] == 0

def test_main_handler_routing(mock_s3_client):
    """Test the main handler routing logic"""
    with patch.dict('os.environ', {'DESTINATION_BUCKET': 'dest-bucket'}):
        # Test full sync routing
        response = handler(MOCK_FULL_SYNC_EVENT, None)
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'statistics' in body
        
        # Test object sync routing
        response = handler(MOCK_OBJECT_SYNC_EVENT, None)
        assert response['statusCode'] == 200
        assert 'S3 copy operation completed successfully' in response['body']

def test_error_handling(mock_s3_client):
    """Test error handling in both handlers"""
    # Simulate S3 error for object_sync
    mock_s3_client.copy_object.side_effect = Exception("S3 Error")
    
    with patch.dict('os.environ', {'DESTINATION_BUCKET': 'dest-bucket'}):
        # Test object sync error handling
        response = object_sync_handler(MOCK_OBJECT_SYNC_EVENT, None)
        assert response['statusCode'] == 500
        assert 'Error in S3 copy operation' in response['body']
        
        # Reset the side effect for full_sync test
        mock_s3_client.copy_object.side_effect = None
        
        # Simulate error in full_sync by causing an exception in list_objects_v2
        mock_s3_client.get_paginator.side_effect = Exception("S3 Error")
        
        # Test full sync error handling
        response = full_sync_handler(MOCK_FULL_SYNC_EVENT, None)
        assert response['statusCode'] == 500
        assert 'Error in S3 sync operation' in response['body']

def test_missing_region_fails(mock_s3_client):
    """Test that full_sync_handler fails when region is not provided"""
    with patch.dict('os.environ', {'DESTINATION_BUCKET': 'dest-bucket'}):
        # Create event missing region
        event_missing_region = {
            'action': 'full_sync',
            'sourceBucket': 'source-bucket',
            'prefix': 'test/'
            # No region specified
        }
        
        # Test full sync handling of missing region
        response = full_sync_handler(event_missing_region, None)
        assert response['statusCode'] == 500
        assert 'Region not specified in event' in response['body'] 