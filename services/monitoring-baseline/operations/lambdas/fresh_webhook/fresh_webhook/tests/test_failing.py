import os
import pytest
from fresh_webhook.tests.helpers import load_event
from fresh_webhook.index import handler

def test_other_event_type():
    event = load_event(os.path.join(os.path.dirname(__file__), 'events', 'unknown_event_type.json'))
    # Expect the handler to raise ValueError for an unhandled event type
    with pytest.raises(ValueError) as excinfo:
        handler(event, None)
    # Optionally, check that the error message is correct
    assert "Unhandled event type" in str(excinfo.value) 