import pytest
import sys
import os
import json
from unittest.mock import MagicMock

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from update_account_principals.index import handler, EventBridgeClient

# Set up environment variables for testing
os.environ['EVENT_BUS_NAME'] = 'test-event-bus'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture
def mock_eventbridge(monkeypatch):
    mock_client = MagicMock()
    initial_policy = {
        "Version": "2012-10-17",
        "Statement": []
    }
    
    def mock_describe_event_bus(*args, **kwargs):
        return {'Policy': json.dumps(initial_policy)}
    
    def mock_put_permission(*args, **kwargs):
        policy = json.loads(kwargs['Policy'])
        initial_policy['Statement'] = policy['Statement']
        return {}
    
    def mock_remove_permission(*args, **kwargs):
        initial_policy['Statement'] = []
        return {}
    
    mock_client.describe_event_bus.side_effect = mock_describe_event_bus
    mock_client.put_permission.side_effect = mock_put_permission
    mock_client.remove_permission.side_effect = mock_remove_permission
    
    def mock_boto3_client(*args, **kwargs):
        return mock_client
    
    monkeypatch.setattr('boto3.client', mock_boto3_client)
    return mock_client

def test_add_account(mock_eventbridge):
    event = {
        'account_id': '123456789012',
        'action': 'add'
    }
    
    # Show initial policy
    initial_policy = mock_eventbridge.describe_event_bus()['Policy']
    print("\nInitial Policy:")
    print(json.dumps(json.loads(initial_policy), indent=2))
    
    response = handler(event, None)
    
    # Show final policy
    final_policy = mock_eventbridge.describe_event_bus()['Policy']
    print("\nFinal Policy:")
    print(json.dumps(json.loads(final_policy), indent=2))
    
    assert response['statusCode'] == 200
    assert 'Successfully added account' in response['body']

def test_add_multiple_accounts(mock_eventbridge):
    # Add first account
    event1 = {
        'account_id': '123456789012',
        'action': 'add'
    }
    print("\nAdding first account...")
    response = handler(event1, None)
    assert response['statusCode'] == 200
    
    # Show policy after first account
    policy_after_first = mock_eventbridge.describe_event_bus()['Policy']
    print("\nPolicy After First Account:")
    print(json.dumps(json.loads(policy_after_first), indent=2))
    
    # Add second account
    event2 = {
        'account_id': '987654321098',
        'action': 'add'
    }
    print("\nAdding second account...")
    response = handler(event2, None)
    assert response['statusCode'] == 200
    
    # Show final policy with both accounts
    final_policy = mock_eventbridge.describe_event_bus()['Policy']
    print("\nFinal Policy With Both Accounts:")
    print(json.dumps(json.loads(final_policy), indent=2))
    
    # Verify both accounts are in the policy
    policy_dict = json.loads(final_policy)
    principals = policy_dict['Statement'][0]['Principal']['AWS']
    assert 'arn:aws:iam::123456789012:root' in principals
    assert 'arn:aws:iam::987654321098:root' in principals

def test_remove_account(mock_eventbridge):
    # First add an account
    add_event = {
        'account_id': '123456789012',
        'action': 'add'
    }
    handler(add_event, None)
    
    # Show policy before removal
    initial_policy = mock_eventbridge.describe_event_bus()['Policy']
    print("\nPolicy Before Removal:")
    print(json.dumps(json.loads(initial_policy), indent=2))
    
    # Remove the account
    remove_event = {
        'account_id': '123456789012',
        'action': 'remove'
    }
    response = handler(remove_event, None)
    
    # Show final policy
    final_policy = mock_eventbridge.describe_event_bus()['Policy']
    print("\nFinal Policy:")
    print(json.dumps(json.loads(final_policy), indent=2))
    
    assert response['statusCode'] == 200
    assert 'Successfully removed account' in response['body']

def test_missing_account_id():
    event = {
        'action': 'add'
    }
    
    response = handler(event, None)
    assert response['statusCode'] == 400
    assert 'Missing account_id' in response['body']

def test_invalid_account_id():
    event = {
        'account_id': 'invalid-id',
        'action': 'add'
    }
    
    response = handler(event, None)
    assert response['statusCode'] == 400
    assert 'Invalid AWS account ID format' in response['body'] 