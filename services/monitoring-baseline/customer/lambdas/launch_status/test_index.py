import json
import os
from unittest.mock import MagicMock, patch
import pytest
from index import (
    handler,
    validate_event,
    get_product_details,
    get_provisioned_products,
    get_all_products,
    process_products,
)

# Load test data
with open('test_data.json', 'r') as f:
    TEST_DATA = json.load(f)

@pytest.fixture
def mock_event():
    return TEST_DATA['events']['with_product_id']

@pytest.fixture
def mock_event_no_product():
    return {
        "region": "us-west-2",
        "product_id": None
    }

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_provisioned_product():
    return TEST_DATA['provisioned_products']['ProvisionedProducts'][0]

@pytest.fixture
def mock_product_detail():
    return TEST_DATA['product_detail']

def test_validate_event_with_product_id():
    event = TEST_DATA['events']['with_product_id']
    region, product_id = validate_event(event)
    assert region == 'us-west-2'
    assert product_id == 'prod-abc123'

def test_validate_event_without_product_id():
    event = TEST_DATA['events']['without_product_id']
    region, product_id = validate_event(event)
    assert region == 'us-west-2'
    assert product_id is None

def test_validate_event_missing_region():
    event = TEST_DATA['events']['missing_region']
    with pytest.raises(ValueError, match="Missing required parameter: region"):
        validate_event(event)

@patch('index.boto3.client')
def test_get_provisioned_products(mock_boto3_client, mock_provisioned_product):
    mock_servicecatalog = MagicMock()
    mock_servicecatalog.search_provisioned_products.return_value = TEST_DATA['provisioned_products']
    mock_boto3_client.return_value = mock_servicecatalog

    result = get_provisioned_products('us-west-2', 'prod-abc123')
    assert result == TEST_DATA['provisioned_products']['ProvisionedProducts']
    mock_servicecatalog.search_provisioned_products.assert_called_once_with(
        Filters={'SearchQuery': ['productId:prod-abc123']}
    )

@patch('index.boto3.client')
def test_get_product_details(mock_boto3_client, mock_product_detail):
    mock_servicecatalog = MagicMock()
    mock_servicecatalog.describe_provisioned_product.return_value = mock_product_detail
    
    # Mock the describe_product API call
    mock_product_response = {
        'ProductViewSummary': {
            'Name': 'Actual Product Name'
        }
    }
    mock_servicecatalog.describe_product.return_value = mock_product_response
    
    mock_boto3_client.return_value = mock_servicecatalog

    result = get_product_details('us-west-2', 'prod-abc123', 'pp-123')
    
    # Verify the API calls
    mock_servicecatalog.describe_provisioned_product.assert_called_once_with(
        Id='pp-123'
    )
    mock_servicecatalog.describe_product.assert_called_once_with(
        Id='prod-abc123'
    )
    
    # Verify the result
    assert result['product_id'] == 'prod-abc123'
    assert result['provisioned_product_id'] == 'pp-123'
    assert result['product_name'] == 'Actual Product Name'
    assert result['provisioned_product_name'] == mock_product_detail['ProvisionedProductDetail'].get('Name', 'N/A')
    assert result['status'] == mock_product_detail['ProvisionedProductDetail'].get('Status', 'N/A')
    assert result['version_name'] == mock_product_detail['ProvisionedProductDetail'].get('ProvisioningArtifactName', 'N/A')
    assert result['provisioned_time'] == str(mock_product_detail['ProvisionedProductDetail'].get('CreatedTime', 'N/A'))

@patch('index.boto3.client')
def test_get_all_products(mock_boto3_client, mock_provisioned_product):
    mock_servicecatalog = MagicMock()
    mock_servicecatalog.search_provisioned_products.return_value = TEST_DATA['provisioned_products']
    mock_boto3_client.return_value = mock_servicecatalog

    result = get_all_products('us-west-2')
    assert result == TEST_DATA['provisioned_products']['ProvisionedProducts']
    mock_servicecatalog.search_provisioned_products.assert_called_once()

@patch('index.get_product_details')
@patch('index.get_provisioned_products')
def test_process_products(mock_get_provisioned_products, mock_get_product_details, mock_provisioned_product, mock_product_detail):
    mock_get_provisioned_products.return_value = [mock_provisioned_product]
    mock_get_product_details.return_value = mock_product_detail['ProvisionedProductDetail']

    result = process_products('us-west-2', 'prod-abc123')
    assert len(result) == 1
    assert result[0]['id'] == mock_provisioned_product['Id']
    assert result[0]['status'] == mock_provisioned_product['Status']
    assert result[0]['name'] == mock_provisioned_product['Name']
    assert result[0]['created_time'] == mock_provisioned_product['CreatedTime']
    assert result[0]['version'] == mock_provisioned_product['ProvisioningArtifactName']

@patch('index.process_products')
@patch('index.validate_event')
def test_handler_with_product_id(mock_validate_event, mock_process_products, mock_event, mock_context, mock_provisioned_product, mock_product_detail):
    mock_validate_event.return_value = ('us-west-2', 'prod-abc123')
    mock_process_products.return_value = [{
        'id': mock_provisioned_product['Id'],
        'status': mock_provisioned_product['Status'],
        'name': mock_provisioned_product['Name'],
        'created_time': mock_provisioned_product['CreatedTime'],
        'version': mock_provisioned_product['ProvisioningArtifactName']
    }]

    response = handler(mock_event, mock_context)
    assert response['statusCode'] == 200
    assert 'body' in response
    body = json.loads(response['body'])
    assert len(body) == 1
    assert body[0]['id'] == mock_provisioned_product['Id']

@patch('index.get_all_products')
@patch('index.validate_event')
def test_handler_without_product_id(mock_validate_event, mock_get_all_products, mock_event_no_product, mock_context, mock_provisioned_product):
    mock_validate_event.return_value = ('us-west-2', None)
    mock_get_all_products.return_value = [mock_provisioned_product]

    response = handler(mock_event_no_product, mock_context)
    assert response['statusCode'] == 200
    assert 'body' in response
    body = json.loads(response['body'])
    assert len(body) == 1
    assert body[0]['id'] == mock_provisioned_product['Id']

@patch('index.validate_event')
def test_handler_missing_region(mock_validate_event, mock_event, mock_context):
    mock_event.pop('region')
    mock_validate_event.side_effect = ValueError("Missing required parameter: region")

    response = handler(mock_event, mock_context)
    assert response['statusCode'] == 400
    assert 'body' in response
    body = json.loads(response['body'])
    assert 'error' in body
    assert body['error'] == "Missing required parameter: region"

@patch('boto3.client')
def test_handler_success(mock_boto3, mock_event, mock_context, mock_provisioned_product, mock_product_detail):
    # Mock Service Catalog client
    mock_sc = MagicMock()
    mock_sc.search_provisioned_products.return_value = {
        'ProvisionedProducts': [mock_provisioned_product]
    }
    mock_sc.describe_provisioned_product.return_value = mock_product_detail
    
    # Mock EventBridge client
    mock_events = MagicMock()
    mock_events.put_events.return_value = {'FailedEntryCount': 0}
    
    def get_client(service, region_name=None):
        if service == 'servicecatalog':
            return mock_sc
        return mock_events
    
    mock_boto3.side_effect = get_client
    
    # Set environment variable
    os.environ['EVENT_BUS_ARN'] = 'arn:aws:events:us-west-2:123456789012:event-bus/test'
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 200
    assert len(json.loads(response['body'])) == 1
    mock_events.put_events.assert_called_once()

@patch('boto3.client')
def test_handler_no_products(mock_boto3, mock_event, mock_context):
    # Mock Service Catalog client
    mock_sc = MagicMock()
    mock_sc.search_provisioned_products.return_value = {
        'ProvisionedProducts': []
    }
    
    # Mock EventBridge client
    mock_events = MagicMock()
    mock_events.put_events.return_value = {'FailedEntryCount': 0}
    
    def get_client(service, region_name=None):
        if service == 'servicecatalog':
            return mock_sc
        return mock_events
    
    mock_boto3.side_effect = get_client
    
    # Set environment variable
    os.environ['EVENT_BUS_ARN'] = 'arn:aws:events:us-west-2:123456789012:event-bus/test'
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 404
    assert 'No provisioned products found' in json.loads(response['body'])['message']
    mock_events.put_events.assert_called_once()

@patch('boto3.client')
def test_handler_missing_event_bus(mock_boto3, mock_event, mock_context):
    if 'EVENT_BUS_ARN' in os.environ:
        del os.environ['EVENT_BUS_ARN']
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 400
    assert 'EVENT_BUS_ARN environment variable is not set' in json.loads(response['body'])['error'] 