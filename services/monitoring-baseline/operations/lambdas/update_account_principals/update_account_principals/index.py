import json
import os
import boto3
import logging
import re
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class EventBridgeClient:
    """Wrapper for AWS EventBridge client operations."""
    def __init__(self, client=None):
        self.client = client or boto3.client('events')

    def describe_event_bus(self, bus_name: str) -> Dict[str, Any]:
        return self.client.describe_event_bus(Name=bus_name)

    def put_permission(self, bus_name: str, policy: str) -> Dict[str, Any]:
        return self.client.put_permission(
            EventBusName=bus_name,
            Policy=policy
        )

    def remove_permission(self, bus_name: str, statement_id: str) -> Dict[str, Any]:
        return self.client.remove_permission(
            EventBusName=bus_name,
            StatementId=statement_id
        )


class PolicyStatement:
    """Value object representing an IAM policy statement."""
    def __init__(self, sid: str, effect: str, principals: List[str], actions: List[str], resource: str):
        self.sid = sid
        self.effect = effect
        self.principals = principals
        self.actions = actions
        self.resource = resource

    @classmethod
    def create_shared_access(cls, bus_name: str) -> 'PolicyStatement':
        # Get region and account ID from the Lambda context
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
        region = boto3.Session().region_name
        
        return cls(
            sid="SharedAccountAccess",
            effect="Allow",
            principals=[],
            actions=["events:PutEvents"],
            resource=f"arn:aws:events:{region}:{account_id}:event-bus/{bus_name}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Sid": self.sid,
            "Effect": self.effect,
            "Principal": {"AWS": self.principals if self.principals else []},
            "Action": self.actions,
            "Resource": self.resource
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyStatement':
        principals = data['Principal']['AWS']
        if isinstance(principals, str):
            principals = [principals]
        return cls(
            sid=data['Sid'],
            effect=data['Effect'],
            principals=[p for p in principals if p],
            actions=data['Action'] if isinstance(data['Action'], list) else [data['Action']],
            resource=data['Resource']
        )


class Policy:
    """Domain object representing an IAM policy."""
    def __init__(self, statements: Optional[List[PolicyStatement]] = None):
        self.version = "2012-10-17"
        self.statements = statements or []

    def add_statement(self, statement: PolicyStatement) -> None:
        self.statements.append(statement)

    def remove_statement(self, sid: str) -> None:
        self.statements = [s for s in self.statements if s.sid != sid]

    def get_statement(self, sid: str) -> Optional[PolicyStatement]:
        return next((s for s in self.statements if s.sid == sid), None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Version": self.version,
            "Statement": [s.to_dict() for s in self.statements]
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> 'Policy':
        if not data:
            return cls()
        statements = [
            PolicyStatement.from_dict(stmt)
            for stmt in data.get('Statement', [])
        ]
        return cls(statements)


class PolicyManager:
    """Manages policy operations and AWS interactions."""
    def __init__(self, event_bridge_client: EventBridgeClient):
        self.client = event_bridge_client

    def get_policy(self, bus_name: str) -> Policy:
        try:
            response = self.client.describe_event_bus(bus_name)
            return Policy.from_dict(json.loads(response.get('Policy', '{}')))
        except Exception as e:
            logger.error(f"Error fetching policy: {str(e)}")
            return Policy()

    def add_account(self, bus_name: str, account_id: str) -> bool:
        """Add an account to the policy."""
        policy = self.get_policy(bus_name)
        stmt = policy.get_statement('SharedAccountAccess')
        if not stmt:
            stmt = PolicyStatement.create_shared_access(bus_name)
            policy.add_statement(stmt)

        account_arn = f"arn:aws:iam::{account_id}:root"
        if account_arn not in stmt.principals:
            stmt.principals.append(account_arn)
            self.client.put_permission(bus_name, json.dumps(policy.to_dict()))
            return True
        return False

    def remove_account(self, bus_name: str, account_id: str) -> bool:
        """Remove an account from the policy."""
        policy = self.get_policy(bus_name)
        stmt = policy.get_statement('SharedAccountAccess')
        if not stmt:
            return False

        account_arn = f"arn:aws:iam::{account_id}:root"
        if account_arn in stmt.principals:
            stmt.principals.remove(account_arn)
            if not stmt.principals:
                self.client.remove_permission(bus_name, 'SharedAccountAccess')
            else:
                self.client.put_permission(bus_name, json.dumps(policy.to_dict()))
            return True
        return False


def validate_account_id(account_id: str) -> bool:
    """Validate AWS account ID format."""
    return bool(re.match(r'^\d{12}$', account_id))


def update_eventbridge_policy(bus_name: str, account_id: str, is_adding: bool = True) -> None:
    """Update the EventBridge policy for the given bus and account."""
    if not validate_account_id(account_id):
        raise ValueError(f"Invalid AWS account ID format: {account_id}")

    manager = PolicyManager(EventBridgeClient())
    
    try:
        if is_adding:
            success = manager.add_account(bus_name, account_id)
            if success:
                logger.info(f"Added account {account_id} to event bus {bus_name}")
            else:
                logger.info(f"Account {account_id} already has access to event bus {bus_name}")
        else:
            success = manager.remove_account(bus_name, account_id)
            if success:
                logger.info(f"Removed account {account_id} from event bus {bus_name}")
            else:
                logger.info(f"Account {account_id} did not have access to event bus {bus_name}")
    except Exception as e:
        logger.error(f"Error updating policy for account {account_id}: {str(e)}")
        raise


def handler(event, context):
    """Lambda handler function."""
    logger.info("Received event: %s", json.dumps(event))
    
    try:
        event_bus_name = os.environ['EVENT_BUS_NAME']
        account_id = event.get('account_id')
        is_adding = event.get('action', 'add').lower() == 'add'
        
        if not account_id:
            error_msg = "Missing account_id in event"
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': error_msg
            }
        
        update_eventbridge_policy(event_bus_name, account_id, is_adding)
        return {
            'statusCode': 200,
            'body': f"Successfully {'added' if is_adding else 'removed'} account {account_id}"
        }
    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        return {
            'statusCode': 400,
            'body': str(e)
        }
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return {
            'statusCode': 500,
            'body': f"Internal server error: {str(e)}"
        }

