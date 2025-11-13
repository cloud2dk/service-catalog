import pytest
from fresh_webhook.event_dispatcher import EventDispatcher

def test_cost_anomaly_event():
    event = {
        "version": "0",
        "id": "12345678-1234-1234-1234-123456789012",
        "detail-type": "CostAnomalyDetected",
        "source": "cloud2.ce.anomaly",
        "account": "123456789012",
        "time": "2024-03-21T12:00:00Z",
        "region": "us-east-1",
        "resources": [],
        "detail": {
            "accountId": "123456789012",
            "anomalyStartDate": "2024-03-21T00:00:00Z",
            "impact": {
                "totalImpact": 100.0,
                "unit": "USD"
            },
            "rootCauses": [
                {
                    "service": "Amazon EC2",
                    "linkedAccount": "123456789012",
                    "linkedAccountName": "Production",
                    "region": "us-east-1",
                    "usageType": "BoxUsage:c4.large",
                    "costCategory": {
                        "name": "Compute",
                        "values": ["EC2"]
                    }
                }
            ],
            "severity": "warning"
        }
    }
    
    dispatcher = EventDispatcher(event)
    result = dispatcher.dispatch()

    assert result is not None
    assert "account_id" in result
    assert "severity" in result
    assert "source_event" in result 