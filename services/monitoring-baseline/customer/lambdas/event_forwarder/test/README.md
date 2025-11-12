# Event Forwarder Lambda Tests

This directory contains tests for the SNS-to-EventBridge event forwarder Lambda.

## Test Structure

### `test_unit.py` - Pure Unit Tests
Tests individual functions without AWS dependencies:
- `extract_sns_message()` - SNS message extraction logic
- `prepare_eventbridge_detail()` - JSON validation and wrapping
- `create_eventbridge_entry()` - EventBridge entry structure
- `send_to_eventbridge()` - EventBridge interaction (minimal mocking)

These tests verify business logic in isolation and run fast without AWS SDK calls.

### `test_integration.py` - Integration Tests
Tests the full `handler()` flow with mocked AWS services:
- End-to-end message forwarding
- CloudWatch alarms, plain text, and cost anomaly messages
- Error handling and validation
- Environment variable configuration
- EventBridge client region selection

These tests verify the complete Lambda execution flow.

## Running Tests

```bash
# Run all tests
pytest test/ -v

# Run only unit tests
pytest test/test_unit.py -v

# Run only integration tests
pytest test/test_integration.py -v

# Run with coverage
pytest test/ --cov=index --cov-report=term-missing
```

## Test Philosophy

The Lambda is designed to be **agnostic** - it forwards any SNS message to EventBridge without inspecting content:
- ✅ All messages use generic `cloud2.events` source
- ✅ All messages use generic `SNSMessage` detail-type
- ✅ Message content is preserved in the `Detail` field
- ✅ Operations account EventBridge rules filter on message content

Tests verify this agnostic behavior is maintained.
