import boto3
import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def validate_event(event: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    region = event.get('region')
    product_id = event.get('product_id')
    
    if not region:
        raise ValueError("Missing required parameter: region")
        
    return region, product_id

def get_all_products(sc_client: boto3.client) -> List[Dict[str, Any]]:
    response = sc_client.search_provisioned_products()
    return response.get('ProvisionedProducts', [])

def get_provisioned_products(sc_client: boto3.client, product_id: str) -> List[Dict[str, Any]]:
    response = sc_client.search_provisioned_products(
        Filters={
            'SearchQuery': [f'productId:{product_id}']
        }
    )
    return response.get('ProvisionedProducts', [])

def get_product_details(sc_client: boto3.client, product_id: str, pp_id: str) -> Dict[str, Any]:
    pp_details = sc_client.describe_provisioned_product(Id=pp_id)
    pp_detail = pp_details.get('ProvisionedProductDetail', {})
    
    # Get the actual product name using describe_product
    product_response = sc_client.describe_product(Id=product_id)
    product_view_summary = product_response.get('ProductViewSummary', {})
    actual_product_name = product_view_summary.get('Name', 'N/A')
    
    return {
        'product_id': product_id,
        'provisioned_product_id': pp_id,
        'product_name': actual_product_name,
        'provisioned_product_name': pp_detail.get('Name', 'N/A'),
        'status': pp_detail.get('Status', 'N/A'),
        'version_name': pp_detail.get('ProvisioningArtifactName', 'N/A'),
        'provisioned_time': str(pp_detail.get('CreatedTime', 'N/A'))
    }

def publish_to_event_bus(eventbridge_client: boto3.client, event_bus_arn: str, detail: Dict[str, Any]) -> None:
    if isinstance(detail, list):
        # For N/A case or empty results, send empty array
        if not detail or (len(detail) == 1 and all(v == 'N/A' for v in detail[0].values() if v != detail[0].get('product_id'))):
            detail_str = json.dumps({
                "provisioned_product": [],
                "num_of_provisioned_product": 0
            })
        else:
            # For successful results with products
            detail_str = json.dumps({
                "provisioned_product": detail,
                "num_of_provisioned_product": len(detail)
            })
    else:
        # For error cases, just pass through the error
        detail_str = json.dumps(detail)
    
    event_entry = {
        'Source': 'cloud2.services',
        'DetailType': 'launch-status',
        'Detail': detail_str,
        'EventBusName': event_bus_arn
    }
    logger.info("Publishing to EventBridge: %s", json.dumps(event_entry))

    response = eventbridge_client.put_events(Entries=[event_entry])
    
    if response.get('FailedEntryCount', 0) > 0:
        logger.error("Failed to send events: %s", json.dumps(response))
        raise Exception("Failed to send events to EventBridge")

    logger.info("Successfully sent event to EventBridge: %s", json.dumps(response))

def build_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }

def process_products(sc_client: boto3.client, product_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if product_id:
        logger.info(f"Searching for provisioned products with product_id: {product_id}")
        provisioned_products = get_provisioned_products(sc_client, product_id)
        if not provisioned_products:
            return []
    else:
        provisioned_products = get_all_products(sc_client)
        
    results = []
    for pp in provisioned_products:
        current_product_id = product_id or pp.get('ProductId', 'N/A')
        result = get_product_details(sc_client, current_product_id, pp['Id'])
        # Ensure version_name is set from the original product data
        if pp.get('ProvisioningArtifactName'):
            result['version_name'] = pp['ProvisioningArtifactName']
        results.append(result)
    
    return results

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("Received event: %s", json.dumps(event))
    
    try:
        region, product_id = validate_event(event)
        
        event_bus_arn = os.getenv('EVENT_BUS_ARN')
        if not event_bus_arn:
            raise ValueError("EVENT_BUS_ARN environment variable is not set")
        event_bus_region = event_bus_arn.split(":")[3]
        
        sc_client = boto3.client('servicecatalog', region_name=region)
        eventbridge_client = boto3.client('events', region_name=event_bus_region)
        
        results = process_products(sc_client, product_id)
        
        if not results:
            try:
                publish_to_event_bus(eventbridge_client, event_bus_arn, [])
            except Exception as e:
                logger.error("Failed to publish empty result to EventBridge: %s", str(e))
            return build_response(404, [])
        
        publish_to_event_bus(eventbridge_client, event_bus_arn, results)
        return build_response(200, results)
        
    except ValueError as e:
        error_result = {"error": str(e)}
        return build_response(400, error_result)
    except Exception as e:
        logger.error("Error: %s", str(e))
        error_result = {"error": str(e)}
        if 'event_bus_arn' in locals() and 'eventbridge_client' in locals():
            try:
                publish_to_event_bus(eventbridge_client, event_bus_arn, error_result)
            except Exception as publish_error:
                logger.error("Failed to publish error to EventBridge: %s", str(publish_error))
        return build_response(500, error_result)
