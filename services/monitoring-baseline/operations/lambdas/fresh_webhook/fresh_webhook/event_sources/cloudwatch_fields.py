from fresh_webhook.event_sources.alert_fields_base import AlertFieldsBase

class CloudwatchFields(AlertFieldsBase):
    def __init__(self, event, alarmTags: dict = {}):

        alarm_data = event.get('alarmData', {})        
        state = alarm_data.get('state', {})
        configuration = alarm_data.get('configuration', {})
        metrics = configuration.get('metrics', [])
        subject = alarm_data.get('alarmName')
        node = metrics[0]['accountId'] if metrics else ''
        description = state.get('reason', '')
        account_id = metrics[0]['accountId'] if metrics else ''
        resource = event.get('alarmArn', '')
        metric_name = metrics[0]['id'] if metrics else ''
        metric_value = state.get('value', '')
        created_at = event.get('time')

        severity_list = [tag.get('Value') for tag in alarmTags if tag.get('Key') == 'severity']
        if not severity_list:
            raise Exception("No 'severity' key found in alarm tags")
        severity = severity_list[0]
        
        super().__init__(
            account_id=account_id,
            region=event.get('region'),
            subject=subject,
            node=node,
            severity=severity,
            description=description,
            resource=resource,
            metric_name=metric_name,
            metric_value=metric_value,
            created_at=created_at,
            source_event=event
        )
