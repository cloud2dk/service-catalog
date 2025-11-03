# Customer Deployment Test - SNS Event Flow

## Overview
This test verifies that SNS messages sent from a customer account are properly received and logged in the operations account CloudWatch.

## Test Steps

### Step 1: Send SNS Message from Customer Account

Execute the following AWS CLI command to publish a test message:

```bash
aws sns publish \
  --topic-arn "arn:aws:sns:eu-west-1:921782004037:cloud2-events" \
  --message '{"test": "message", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' \
  --profile paperturn-web-jump \
  --region eu-west-1
```

Expected output:
```json
{
    "MessageId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Step 2: Wait for Message Processing

Wait 30-60 seconds for the message to be processed and appear in CloudWatch logs.

```bash
sleep 45
```

### Step 3: Verify Message in Operations Account CloudWatch

Check the CloudWatch logs in the operations account for the SNS message:

1. Switch to operations account profile
2. Navigate to CloudWatch Logs
3. Look for log group related to cloud2-events processing
4. Verify the test message with current timestamp appears in the logs

## Expected Results

- SNS publish command returns a MessageId
- After waiting period, the test message appears in operations account CloudWatch logs
- Message contains the current timestamp and test payload
- No errors in the processing pipeline

## Troubleshooting

If the test fails:
- Verify AWS credentials and profile configuration
- Check SNS topic permissions
- Confirm operations account CloudWatch log group exists
- Review IAM roles for cross-account access
