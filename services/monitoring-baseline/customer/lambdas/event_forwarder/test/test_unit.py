import json
import pytest
import sys
from pathlib import Path

# Add parent directory to path to import index module
sys.path.insert(0, str(Path(__file__).parent.parent))

import index


# Sample CloudWatch Alarm message (most common use case)
CLOUDWATCH_ALARM_MESSAGE = json.dumps({
    "AlarmName": "HighCPUUtilization",
    "AlarmDescription": "CPU utilization is above 80%",
    "AWSAccountId": "123456789012",
    "NewStateValue": "ALARM",
    "NewStateReason": "Threshold Crossed",
    "StateChangeTime": "2025-11-12T10:00:00.000+0000",
    "Region": "us-east-1",
    "AlarmArn": "arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighCPUUtilization",
    "Trigger": {
        "MetricName": "CPUUtilization",
        "Namespace": "AWS/EC2",
        "StatisticType": "Statistic",
        "Statistic": "AVERAGE",
        "Dimensions": [{"name": "InstanceId", "value": "i-1234567890abcdef0"}],
        "Period": 300,
        "EvaluationPeriods": 2,
        "ComparisonOperator": "GreaterThanThreshold",
        "Threshold": 80.0
    }
})

PLAIN_TEXT_MESSAGE = "This is a plain text notification"

COST_ANOMALY_MESSAGE = json.dumps({
    "anomalyId": "abc-123",
    "anomalyScore": 85.5,
    "impact": {"maxImpact": 100.50},
    "rootCauses": []
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


class TestExtractSnsMessage:
    def test_extract_valid_message(self):
        event = create_sns_event(CLOUDWATCH_ALARM_MESSAGE)
        result = index.extract_sns_message(event)
        assert result == CLOUDWATCH_ALARM_MESSAGE

    def test_extract_from_empty_records(self):
        event = {'Records': []}
        with pytest.raises(ValueError, match="Invalid SNS event structure"):
            index.extract_sns_message(event)

    def test_extract_from_missing_sns_key(self):
        event = {'Records': [{'NotSns': {}}]}
        with pytest.raises(ValueError, match="Invalid SNS event structure"):
            index.extract_sns_message(event)

    def test_extract_from_missing_message_key(self):
        event = {'Records': [{'Sns': {'NotMessage': 'test'}}]}
        with pytest.raises(ValueError, match="Invalid SNS event structure"):
            index.extract_sns_message(event)


class TestPrepareEventbridgeDetail:
    def test_valid_json_passthrough(self):
        result = index.prepare_eventbridge_detail(CLOUDWATCH_ALARM_MESSAGE)
        assert result == CLOUDWATCH_ALARM_MESSAGE
        parsed = json.loads(result)
        assert parsed['AlarmName'] == 'HighCPUUtilization'

    def test_plain_text_wrapped(self):
        result = index.prepare_eventbridge_detail(PLAIN_TEXT_MESSAGE)
        parsed = json.loads(result)
        assert parsed['message'] == PLAIN_TEXT_MESSAGE

    def test_empty_string_wrapped(self):
        result = index.prepare_eventbridge_detail("")
        parsed = json.loads(result)
        assert parsed['message'] == ""

    def test_invalid_json_wrapped(self):
        invalid_json = '{"incomplete": '
        result = index.prepare_eventbridge_detail(invalid_json)
        parsed = json.loads(result)
        assert parsed['message'] == invalid_json

    def test_cost_anomaly_passthrough(self):
        result = index.prepare_eventbridge_detail(COST_ANOMALY_MESSAGE)
        assert result == COST_ANOMALY_MESSAGE
        parsed = json.loads(result)
        assert parsed['anomalyId'] == 'abc-123'


class TestCreateEventbridgeEntry:
    def test_entry_structure(self):
        detail = CLOUDWATCH_ALARM_MESSAGE
        event_bus_arn = 'arn:aws:events:eu-west-1:999999999999:event-bus/operations-event-bus'

        entry = index.create_eventbridge_entry(detail, event_bus_arn)

        assert entry['Source'] == 'cloud2.events'
        assert entry['DetailType'] == 'SNSMessage'
        assert entry['Detail'] == detail
        assert entry['EventBusName'] == event_bus_arn

    def test_generic_source_for_all_messages(self):
        detail = COST_ANOMALY_MESSAGE
        event_bus_arn = 'arn:aws:events:us-east-1:123456789012:event-bus/test-bus'

        entry = index.create_eventbridge_entry(detail, event_bus_arn)

        assert entry['Source'] == 'cloud2.events'
        assert entry['DetailType'] == 'SNSMessage'

    def test_detail_passthrough(self):
        detail = json.dumps({"test": "data", "nested": {"value": 123}})
        event_bus_arn = 'arn:aws:events:us-east-1:123456789012:event-bus/test-bus'

        entry = index.create_eventbridge_entry(detail, event_bus_arn)

        assert entry['Detail'] == detail
        assert json.loads(entry['Detail'])['test'] == 'data'


class TestSendToEventbridge:
    def test_successful_send(self):
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.put_events.return_value = {'FailedEntryCount': 0}

        event_entry = {
            'Source': 'cloud2.events',
            'DetailType': 'SNSMessage',
            'Detail': '{"test": "data"}',
            'EventBusName': 'arn:aws:events:us-east-1:123456789012:event-bus/test'
        }

        index.send_to_eventbridge(mock_client, event_entry)

        mock_client.put_events.assert_called_once_with(Entries=[event_entry])

    def test_failed_send_raises_exception(self):
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.put_events.return_value = {
            'FailedEntryCount': 1,
            'Entries': [{'ErrorCode': 'InternalException'}]
        }

        event_entry = {
            'Source': 'cloud2.events',
            'DetailType': 'SNSMessage',
            'Detail': '{"test": "data"}',
            'EventBusName': 'arn:aws:events:us-east-1:123456789012:event-bus/test'
        }

        with pytest.raises(Exception, match="Failed to send events to EventBridge"):
            index.send_to_eventbridge(mock_client, event_entry)
