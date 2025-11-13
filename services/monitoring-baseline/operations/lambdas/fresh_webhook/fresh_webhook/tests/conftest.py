import pytest
import os
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_aws_and_fresh_services():
    """Mock AWS and Freshservice calls for all tests."""
    # Set required environment variable
    os.environ['FRESH_WEBHOOK_SECRET'] = 'test-secret'

    # Mock AWS Secrets Manager
    with patch('fresh_webhook.helpers.aws_helpers.get_secret_value') as mock_secret:
        mock_secret.return_value = {
            'auth_key': 'test-auth-key',
            'endpoint': 'https://test.freshservice.com/webhook'
        }

        # Mock CloudWatch tags
        with patch('fresh_webhook.helpers.aws_helpers.get_cloudwatch_alarm_tags') as mock_tags:
            mock_tags.return_value = [
                {'Key': 'Environment', 'Value': 'test'},
                {'Key': 'Service', 'Value': 'test-service'},
                {'Key': 'severity', 'Value': 'critical'}
            ]

            # Mock Freshservice HTTP request
            with patch('fresh_webhook.helpers.fresh_helpers.send_event') as mock_send:
                mock_send.return_value = 'Ticket created successfully'

                yield {
                    'secret': mock_secret,
                    'tags': mock_tags,
                    'send_event': mock_send
                }

    # Cleanup
    if 'FRESH_WEBHOOK_SECRET' in os.environ:
        del os.environ['FRESH_WEBHOOK_SECRET']
