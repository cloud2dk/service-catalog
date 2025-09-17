import json

from fresh_webhook.event_sources.alert_fields_base import AlertFieldsBase

class EventBridgeFields(AlertFieldsBase):
    def __init__(self, event):
        
        event_source = event.get('source')
        account_id = event.get('account')
        region = event.get('region')
        created_at = event.get('time')
        severity = event.get('severity')
        detail = event.get('detail', {})  # Default to empty dict if detail is missing

        event_name = detail.get('eventName') or ''
                      
        subject = f"{event_source}:{event_name}"
        description = json.dumps(event, indent=2)
        resource = f"{event_source}:{event_name}"
                
        super().__init__(
            account_id=account_id,
            region=region,
            subject=subject,
            node=account_id,
            severity=severity,
            description=description,
            resource=resource,
            metric_name=event_name,
            metric_value=1,
            created_at=created_at,
            source_event=event
        )