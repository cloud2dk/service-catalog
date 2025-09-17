class AlertFieldsBase:
    def __init__(self, account_id, region, subject, node, severity, description, resource, metric_name, metric_value, created_at, source_event):
        self.account_id = account_id
        self.region  = region
        self.subject = subject
        self.node = node
        self.severity = severity
        self.description = description
        self.resource = resource
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.created_at = created_at
        self.source_event = source_event
        
    def to_dict(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "subject": self.subject,
            "node": self.node,
            "severity": self.severity,
            "description": self.description,
            "resource": self.resource,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "created_at": self.created_at,
            "source_event": self.source_event
        }
        