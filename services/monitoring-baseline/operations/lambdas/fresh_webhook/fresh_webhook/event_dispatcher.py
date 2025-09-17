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

    def _send_to_fresh(self, event):
        secret_name = os.environ.get('FRESH_WEBHOOK_SECRET')    
        if not secret_name:
            raise ValueError("Secret name not found in environment variables")
            
        secret = aws_helpers.get_secret_value(secret_name)
        print("Sending event to Fresh Webhook")
        
        # Format the event using the template
        formatted_html = self.formatter.format_event(event)
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

    def default_handler(self):
        # Print the event type (or lack thereof) and raise an exception
        event_source = self.event.get("source", "Unknown")
        error_message = f"Unhandled event type: {event_source}"
        print(error_message)
        raise ValueError(error_message)  # You can choose the appropriate exception type

    def dispatch(self):
        sources = {
            "aws.cloudwatch": self.handle_cloudwatch_alarm,
            "aws.health": self.handle_aws_health_event,
            "aws.guardduty": self.handle_guardduty_event,
            "aws.backup": self.backup_failed_event,
            "cloud2.ce.anomaly": self.handle_ce_anomaly_event
        }
        handler = sources.get(self.event.get("source"), self.default_handler)
        return handler()