import os
from fresh_webhook.index import handler
from fresh_webhook.tests.helpers import load_event

def test_guardduty_event ():
    event = load_event(os.path.join(os.path.dirname(__file__), 'events', 'guardduty_event.json'))
    response = handler(event, None)
    assert response['statusCode'] == 200 