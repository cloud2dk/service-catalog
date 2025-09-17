import json
import os
import pytest
import boto3
from index import (
    handler,
    validate_event,
    get_product_details,
    get_provisioned_products,
    get_all_products,
    process_products,
)

def load_test_data(filename):
    """Load test data from a JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def test_data_product():
    """Load test data with product ID."""
    return load_test_data('test_data_product.json')

@pytest.fixture
def test_data_region():
    """Load test data with only region."""
    return load_test_data('test_data_region.json')

def test_get_all_products_integration(test_data_region):
    """Integration test that makes actual AWS Service Catalog calls to list all products."""
    sc_client = boto3.client('servicecatalog', region_name=test_data_region['region'])
    products = get_all_products(sc_client)
    
    # Verify the response structure
    assert isinstance(products, list)
    if products:  # If there are any products
        product = products[0]
        assert 'Id' in product
        assert 'Status' in product
        assert 'Name' in product
        assert 'CreatedTime' in product
        assert 'ProvisioningArtifactName' in product
        assert 'ProductId' in product

def test_get_provisioned_products_integration(test_data_region):
    """Integration test that makes actual AWS Service Catalog calls to get products for a specific ID."""
    sc_client = boto3.client('servicecatalog', region_name=test_data_region['region'])
    all_products = get_all_products(sc_client)
    if not all_products:
        pytest.skip("No products available for testing")
    
    # Use the first product's ProductId for testing
    product = all_products[0]
    if 'ProductId' not in product:
        pytest.skip("Product ID not available in the product details")
    
    product_id = product['ProductId']
    products = get_provisioned_products(sc_client, product_id)
    
    # Verify the response structure
    assert isinstance(products, list)
    assert len(products) > 0
    product = products[0]
    assert 'Id' in product
    assert 'Status' in product
    assert 'Name' in product
    assert 'CreatedTime' in product
    assert 'ProvisioningArtifactName' in product

def test_get_product_details_integration(test_data_region):
    """Integration test that makes actual AWS Service Catalog calls to get product details."""
    sc_client = boto3.client('servicecatalog', region_name=test_data_region['region'])
    all_products = get_all_products(sc_client)
    if not all_products:
        pytest.skip("No products available for testing")
    
    provisioned_product_id = all_products[0]['Id']
    product_id = all_products[0]['ProductId']
    details = get_product_details(sc_client, product_id, provisioned_product_id)
    
    assert isinstance(details, dict)
    assert 'product_id' in details
    assert 'provisioned_product_id' in details
    assert 'product_name' in details
    assert 'provisioned_product_name' in details
    assert 'status' in details
    assert 'version_name' in details
    assert 'provisioned_time' in details

def test_handler_integration_all_products(test_data_region):
    response = handler(test_data_region, {})
    
    assert response['statusCode'] in [200, 404]
    assert 'body' in response
    
    body = json.loads(response['body'])
    assert isinstance(body, list)
    if response['statusCode'] == 200:
        if body:
            product = body[0]
            assert 'product_id' in product
            assert 'provisioned_product_id' in product
            assert 'product_name' in product
            assert 'status' in product
            assert 'version_name' in product
            assert 'provisioned_time' in product
    else:  # 404
        assert len(body) == 0

def test_handler_integration_specific_product(test_data_product):
    response = handler(test_data_product, {})
    
    assert response['statusCode'] in [200, 404]
    assert 'body' in response
    
    body = json.loads(response['body'])
    assert isinstance(body, list)
    if response['statusCode'] == 200:
        assert len(body) > 0
        product = body[0]
        assert 'product_id' in product
        assert 'provisioned_product_id' in product
        assert 'product_name' in product
        assert 'status' in product
        assert 'version_name' in product
        assert 'provisioned_time' in product
    else:  # 404
        assert len(body) == 0

def test_handler_integration_invalid_product(test_data_region):
    invalid_data = test_data_region.copy()
    invalid_data['product_id'] = 'prod-invalid-id'
    
    response = handler(invalid_data, {})
    
    assert response['statusCode'] == 404
    assert 'body' in response
    
    body = json.loads(response['body'])
    assert isinstance(body, list)
    assert len(body) == 0 