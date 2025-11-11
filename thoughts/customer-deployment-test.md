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

## Security Hub Manual Test

### Step 4: Send Manual Security Hub Finding

Execute the following AWS CLI command to create a test Security Hub finding:

```bash
aws securityhub batch-import-findings \
  --findings '[{
    "SchemaVersion": "2018-10-08",
    "Id": "manual-test-'$(date +%s)'",
    "ProductArn": "arn:aws:securityhub:'${AWS_DEFAULT_REGION}':'$(aws sts get-caller-identity --query Account --output text)':product/'$(aws sts get-caller-identity --query Account --output text)'/default",
    "GeneratorId": "manual-test-generator",
    "AwsAccountId": "'$(aws sts get-caller-identity --query Account --output text)'",
    "Types": ["Unusual Behaviors/Application"],
    "Title": "Manual Test Security Event",
    "Description": "Manual test event to verify Security Hub to Fresh integration",
    "Severity": {"Label": "MEDIUM"},
    "Confidence": 100,
    "Criticality": 50,
    "CreatedAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "UpdatedAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "Resources": [{
      "Id": "arn:aws:lambda:'${AWS_DEFAULT_REGION}':'$(aws sts get-caller-identity --query Account --output text)':function:manual-test",
      "Type": "AwsLambdaFunction",
      "Region": "'${AWS_DEFAULT_REGION}'"
    }]
  }]' \
  --profile paperturn-web-jump \
  --region eu-west-1
```

### Step 5: Verify in Fresh

Check Fresh for the new ticket created from the Security Hub finding within 2-3 minutes.

## Troubleshooting

If the test fails:
- Verify AWS credentials and profile configuration
- Check SNS topic permissions
- Confirm operations account CloudWatch log group exists
- Review IAM roles for cross-account access
- For Security Hub: Ensure Security Hub is enabled and has proper EventBridge rules configured
