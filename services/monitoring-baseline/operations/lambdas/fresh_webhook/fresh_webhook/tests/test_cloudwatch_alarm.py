import os
from fresh_webhook.tests.helpers import load_event
from fresh_webhook.index import handler

def test_cloudwatch_alarm ():  
    event = load_event(os.path.join(os.path.dirname(__file__), 'events', 'cloudwatch_alarm.json'))
    response = handler(event, None)
    assert response['statusCode'] == 200 