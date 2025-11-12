import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import index module
sys.path.insert(0, str(Path(__file__).parent.parent))

import index


# Sample messages
CLOUDWATCH_ALARM_MESSAGE = json.dumps({
    "AlarmName": "HighCPUUtilization",
    "NewStateValue": "ALARM",
    "Region": "us-east-1"
})

PLAIN_TEXT_MESSAGE = "This is a plain text notification"

COST_ANOMALY_MESSAGE = json.dumps({
    "anomalyId": "abc-123",
    "anomalyScore": 85.5
})


def create_sns_event(message):
    return {
        'Records': [{
            'Sns': {
                'Message': message,
                'TopicArn': 'arn:aws:sns:us-east-1:123456789012:test-topic',
                'MessageId': 'test-message-id',
                'Timestamp': '2025-11-12T10:00:00.000Z',
                'Subject': 'Test Subject'
            }
        }]
    }


class TestHandlerIntegration:
    @patch.dict('os.environ', {'EVENT_BUS_ARN': 'arn:aws:events:eu-west-1:999999999999:event-bus/operations-event-bus'})
    @patch('boto3.client')
    def test_cloudwatch_alarm_end_to_end(self, mock_boto_client):
        mock_eventbridge = MagicMock()
        mock_eventbridge.put_events.return_value = {'FailedEntryCount': 0, 'Entries': []}
        mock_boto_client.return_value = mock_eventbridge

        event = create_sns_event(CLOUDWATCH_ALARM_MESSAGE)
        result = index.handler(event, None)

        assert result['statusCode'] == 200
        assert result['body'] == 'Event sent to EventBridge successfully!'

        mock_eventbridge.put_events.assert_called_once()
        call_args = mock_eventbridge.put_events.call_args[1]['Entries'][0]

        assert call_args['Source'] == 'cloud2.events'
        assert call_args['DetailType'] == 'SNSMessage'
        assert call_args['EventBusName'] == 'arn:aws:events:eu-west-1:999999999999:event-bus/operations-event-bus'

        detail = json.loads(call_args['Detail'])
        assert detail['AlarmName'] == 'HighCPUUtilization'
        assert detail['NewStateValue'] == 'ALARM'

    @patch.dict('os.environ', {'EVENT_BUS_ARN': 'arn:aws:events:eu-west-1:999999999999:event-bus/operations-event-bus'})
    @patch('boto3.client')
    def test_plain_text_message_end_to_end(self, mock_boto_client):
        mock_eventbridge = MagicMock()
        mock_eventbridge.put_events.return_value = {'FailedEntryCount': 0, 'Entries': []}
        mock_boto_client.return_value = mock_eventbridge

        event = create_sns_event(PLAIN_TEXT_MESSAGE)
        result = index.handler(event, None)

        assert result['statusCode'] == 200

        call_args = mock_eventbridge.put_events.call_args[1]['Entries'][0]
        detail = json.loads(call_args['Detail'])
        assert detail['message'] == PLAIN_TEXT_MESSAGE

    @patch.dict('os.environ', {'EVENT_BUS_ARN': 'arn:aws:events:eu-west-1:999999999999:event-bus/operations-event-bus'})
    @patch('boto3.client')
    def test_cost_anomaly_uses_generic_source(self, mock_boto_client):
        mock_eventbridge = MagicMock()
        mock_eventbridge.put_events.return_value = {'FailedEntryCount': 0, 'Entries': []}
        mock_boto_client.return_value = mock_eventbridge

        event = create_sns_event(COST_ANOMALY_MESSAGE)
        index.handler(event, None)

        call_args = mock_eventbridge.put_events.call_args[1]['Entries'][0]
        assert call_args['Source'] == 'cloud2.events'
        assert call_args['DetailType'] == 'SNSMessage'

        detail = json.loads(call_args['Detail'])
        assert detail['anomalyId'] == 'abc-123'

    @patch.dict('os.environ', {'EVENT_BUS_ARN': 'arn:aws:events:us-east-1:123456789012:event-bus/ops-bus'})
    @patch('boto3.client')
    def test_eventbridge_client_uses_correct_region(self, mock_boto_client):
        mock_eventbridge = MagicMock()
        mock_eventbridge.put_events.return_value = {'FailedEntryCount': 0}
        mock_boto_client.return_value = mock_eventbridge

        event = create_sns_event(CLOUDWATCH_ALARM_MESSAGE)
        index.handler(event, None)

        mock_boto_client.assert_called_once_with('events', region_name='us-east-1')

    @patch.dict('os.environ', {'EVENT_BUS_ARN': 'arn:aws:events:eu-west-1:999999999999:event-bus/ops-bus'})
    @patch('boto3.client')
    def test_eventbridge_failure_handling(self, mock_boto_client):
        mock_eventbridge = MagicMock()
        mock_eventbridge.put_events.return_value = {
            'FailedEntryCount': 1,
            'Entries': [{'ErrorCode': 'MalformedDetail', 'ErrorMessage': 'Detail is malformed.'}]
        }
        mock_boto_client.return_value = mock_eventbridge

        event = create_sns_event(CLOUDWATCH_ALARM_MESSAGE)

        with pytest.raises(Exception, match="Failed to send events to EventBridge"):
            index.handler(event, None)

    @patch.dict('os.environ', {})
    def test_missing_event_bus_arn_environment_variable(self):
        event = create_sns_event(CLOUDWATCH_ALARM_MESSAGE)

        with pytest.raises(ValueError, match="EVENT_BUS_ARN environment variable is not set"):
            index.handler(event, None)

    @patch.dict('os.environ', {'EVENT_BUS_ARN': 'arn:aws:events:eu-west-1:999999999999:event-bus/ops-bus'})
    def test_invalid_sns_event_structure(self):
        invalid_event = {'Records': []}

        with pytest.raises(ValueError, match="Invalid SNS event structure"):
            index.handler(invalid_event, None)

    @patch.dict('os.environ', {'EVENT_BUS_ARN': 'arn:aws:events:eu-west-1:999999999999:event-bus/ops-bus'})
    def test_missing_records_key(self):
        invalid_event = {'NotRecords': []}

        with pytest.raises(ValueError, match="Invalid SNS event structure"):
            index.handler(invalid_event, None)
