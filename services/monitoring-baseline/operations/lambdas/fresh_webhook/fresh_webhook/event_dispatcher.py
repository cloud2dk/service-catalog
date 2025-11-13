import os
import json
from datetime import datetime
from dateutil import parser
from jinja2 import Environment, FileSystemLoader, select_autoescape

from fresh_webhook.event_sources.cloudwatch_fields import CloudwatchFields
from fresh_webhook.event_sources.eventbridge_fields import EventBridgeFields
from fresh_webhook.helpers import aws_helpers, fresh_helpers


class EventFormatter:
    def __init__(self):
        self.env = self._setup_jinja_env()
        self.template = self._load_template()
    
    def _setup_jinja_env(self):
        env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        env.filters['tojson'] = lambda obj, **kwargs: json.dumps(obj, indent=2)
        env.filters['datetime'] = lambda dt: dt if not dt else parser.parse(str(dt)).strftime("%Y-%m-%d %H:%M:%S %Z")
        env.globals['now'] = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        return env
    
    def _load_template(self):
        return self.env.get_template('event.html.j2')
    
    def format_event(self, event):
        return self.template.render(event=event)


class EventDispatcher:
    def __init__(self, event):
        self.event = event
        self.formatter = EventFormatter()

    def _send_to_fresh(self, fields_or_event):
        secret_name = os.environ.get('FRESH_WEBHOOK_SECRET')
        if not secret_name:
            raise ValueError("Secret name not found in environment variables")

        secret = aws_helpers.get_secret_value(secret_name)
        print("Sending event to Fresh Webhook")

        # Template expects raw EventBridge event structure
        # Extract source_event if we received a fields dict from EventBridgeFields.to_dict()
        if isinstance(fields_or_event, dict) and 'source_event' in fields_or_event:
            template_data = fields_or_event['source_event']
        else:
            template_data = fields_or_event

        # Format the event using the template
        formatted_html = self.formatter.format_event(template_data)
        print("Formatted HTML:")
        print(formatted_html)

        # Send to Freshservice with HTML content type
        headers = {
            'Authorization': secret['auth_key'],
            'Content-Type': 'text/html'
        }
        response = fresh_helpers.send_event(formatted_html, secret, headers)
        return response

    def handle_cloudwatch_alarm(self):
        print("Event Type: CloudWatch Alarm")
        tags = aws_helpers.get_cloudwatch_alarm_tags(self.event["alarmArn"])
        fields = CloudwatchFields(self.event, tags).to_dict()
        self._send_to_fresh(fields)
        return fields

    def handle_aws_health_event(self):
        print("Event Type: AWS Health Event")
        # Access and print details specific to AWS Health events
        print("Event Details:", self.event["detail"]["eventDescription"][0]["latestDescription"])
        fields = EventBridgeFields(self.event).to_dict()
        self._send_to_fresh(fields)
        return fields

    def handle_guardduty_finding_event(self):
        print("Event Type: GuardDuty Finding")        
        print("Severity:", self.event["detail"]["severity"])
        # map severity to Freshservice severity:
        # 1-4: warning, 4-7: error, 7-10: critical
        severity = self.event["detail"]["severity"]
        if severity < 4:
            self.event["severity"] = "warning"
        elif severity < 7:
            self.event["severity"] = "error"
        else:
            self.event["severity"] = "critical"

        self.event["detail"]["eventName"] = "GuardDutyFinding"
        fields = EventBridgeFields(self.event).to_dict()
        self._send_to_fresh(fields) 
        return self.event
    
    def handle_guardduty_event(self):
        print("Event Type: GuardDuty Event")        
        if self.event["detail-type"] == "GuardDuty Finding":
            return self.handle_guardduty_finding_event()
        
        elif self.event["detail"]["eventName"] in ["UpdateDetector", "DeleteDetector"]:
            print("GuardDuty may be disabled, setting severity to error")
            self.event["severity"] = "error"
            fields = EventBridgeFields(self.event).to_dict()
            self._send_to_fresh(fields)
            return self.event
        else:
            print("Unknown GuardDuty event type, seetting severity to warning")
            self.event["severity"] = "warning"
            return self.event
 
    def handle_ce_anomaly_event(self):
        print("Event Type: Cost Explorer Anomaly")
        self.event["severity"] = "warning"
        # detail.event_name is missing in the event, so we add it
        self.event["detail"]["eventName"] = "CostAnomalyDetected"
        fields = EventBridgeFields(self.event).to_dict()        
        self._send_to_fresh(fields)
        return fields
    
    def backup_failed_event(self):
        print("Event Type: Backup Failed")
        self.event["severity"] = "warning"
        self.event["detail"]["eventName"] = "BackupFailed"
        fields = EventBridgeFields(self.event).to_dict()
        self._send_to_fresh(fields)
        return fields

    def handle_securityhub_event(self):
        print(f"[HANDLER] Processing Security Hub Finding - source: {self.event.get('source')}, detail-type: {self.event.get('detail-type')}")

        # Security Hub findings have severity in detail.findings[].Severity.Label
        # Map Security Hub severity to Freshservice severity
        try:
            finding = self.event.get("detail", {})
            if "findings" in finding and len(finding["findings"]) > 0:
                severity_label = finding["findings"][0].get("Severity", {}).get("Label", "MEDIUM")
                finding_id = finding["findings"][0].get("Id", "unknown")
                finding_type = finding["findings"][0].get("Types", ["unknown"])[0] if finding["findings"][0].get("Types") else "unknown"
            else:
                severity_label = "MEDIUM"
                finding_id = "unknown"
                finding_type = "unknown"

            # Map Security Hub severity labels to Freshservice severity
            if severity_label in ["INFORMATIONAL", "LOW"]:
                mapped_severity = "warning"
            elif severity_label == "MEDIUM":
                mapped_severity = "error"
            else:  # HIGH, CRITICAL
                mapped_severity = "critical"

            self.event["severity"] = mapped_severity

            print(f"[HANDLER] Security Hub - ID: {finding_id}, Type: {finding_type}, Severity: {severity_label} -> {mapped_severity}")

        except (KeyError, IndexError) as e:
            print(f"[ERROR] Failed to extract Security Hub severity, using default 'error': {e}")
            self.event["severity"] = "error"

        self.event["detail"]["eventName"] = "SecurityHubFinding"
        fields = EventBridgeFields(self.event).to_dict()
        self._send_to_fresh(fields)

        print(f"[HANDLER] Security Hub Finding sent to Freshservice successfully")
        return fields

    def handle_sns_wrapped_event(self):
        print(f"[HANDLER] Processing SNS-Wrapped Event - source: {self.event.get('source')}, detail-type: {self.event.get('detail-type')}")

        # EventBridge already parsed the Detail JSON string into a dict
        nested_event = self.event.get("detail")
        if not nested_event:
            print(f"[ERROR] SNS-wrapped event has no detail field")
            raise ValueError("SNS-wrapped event has no detail field")

        nested_source = nested_event.get("source")
        nested_detail_type = nested_event.get("detail-type")
        print(f"[HANDLER] Unwrapping nested event - source: {nested_source}, detail-type: {nested_detail_type}")

        # Route based on the nested event's source
        if nested_source == "aws.cost-anomaly-detection":
            print(f"[HANDLER] Routing to Cost Anomaly handler")
            # Replace the event with the nested event and call anomaly handler
            self.event = nested_event
            return self.handle_ce_anomaly_event()
        else:
            error_message = f"Unhandled nested event source in SNS wrapper: {nested_source}"
            print(f"[ERROR] {error_message}")
            raise ValueError(error_message)

    def default_handler(self):
        # Print the event type (or lack thereof) and raise an exception
        event_source = self.event.get("source", "Unknown")
        error_message = f"Unhandled event type: {event_source}"
        print(error_message)
        raise ValueError(error_message)  # You can choose the appropriate exception type

    def dispatch(self):
        event_source = self.event.get("source", "Unknown")
        event_detail_type = self.event.get("detail-type", "Unknown")
        event_account = self.event.get("account", "Unknown")
        event_region = self.event.get("region", "Unknown")

        print(f"[DISPATCH] Received event - source: {event_source}, detail-type: {event_detail_type}, account: {event_account}, region: {event_region}")

        sources = {
            "aws.cloudwatch": self.handle_cloudwatch_alarm,
            "aws.health": self.handle_aws_health_event,
            "aws.guardduty": self.handle_guardduty_event,
            "aws.backup": self.backup_failed_event,
            "aws.securityhub": self.handle_securityhub_event,
            "cloud2.events": self.handle_sns_wrapped_event,
            "cloud2.ce.anomaly": self.handle_ce_anomaly_event
        }

        handler = sources.get(event_source, self.default_handler)
        print(f"[DISPATCH] Routing to handler: {handler.__name__}")

        return handler()