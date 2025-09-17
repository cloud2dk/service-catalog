import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC
from customer_events.index import handler, process_event

# Mock event for testing
MOCK_EVENT = {
    'id': 'test-123',
    'data': 'test data'
}

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv('EVENT_BUCKET', 'test-bucket')
    return 'test-bucket'

@pytest.fixture
def mock_s3():
    mock_client = MagicMock()
    with patch('boto3.client', return_value=mock_client):
        yield mock_client

@pytest.fixture
def mock_datetime():
    with patch('customer_events.index.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2025, 3, 31, 12, 0, 0, tzinfo=UTC)
        yield mock_dt

def test_process_event_success(mock_env, mock_s3, mock_datetime):
    """Test successful event processing"""
    response = process_event(MOCK_EVENT)
    
    # Verify S3 put_object was called correctly
    mock_s3.put_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='events/2025/03/31/test-123',
        Body=json.dumps(MOCK_EVENT),
        ContentType='application/json'
    )
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'Success'
    assert body['event_id'] == 'test-123'
    assert body['location'] == 's3://test-bucket/events/2025/03/31/test-123'

def test_process_event_missing_id(mock_env, mock_s3):
    """Test error handling when event is missing id"""
    event_without_id = {'data': 'test'}
    response = process_event(event_without_id)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert "Event must contain an 'id' field" in body['error']
    mock_s3.put_object.assert_not_called()

def test_process_event_missing_bucket(monkeypatch, mock_s3):
    """Test error handling when EVENT_BUCKET is not set"""
    monkeypatch.delenv('EVENT_BUCKET', raising=False)
    response = process_event(MOCK_EVENT)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert "EVENT_BUCKET environment variable is not set" in body['error']
    mock_s3.put_object.assert_not_called()

def test_process_event_s3_error(mock_env, mock_s3):
    """Test error handling when S3 operation fails"""
    mock_s3.put_object.side_effect = Exception("S3 Error")
    response = process_event(MOCK_EVENT)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert "S3 Error" in body['error']

def test_handler_success(mock_env, mock_s3, mock_datetime):
    """Test successful handler execution"""
    response = handler(MOCK_EVENT, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'Success'
    assert body['event_id'] == 'test-123'
    assert body['location'] == 's3://test-bucket/events/2025/03/31/test-123'

def test_process_event_error():
    """Test error handling in event processing"""
    # Simulate an error by passing None
    response = process_event(None)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body

def test_handler_error():
    """Test error handling in handler"""
    # Simulate an error by passing None
    response = handler(None, None)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body 