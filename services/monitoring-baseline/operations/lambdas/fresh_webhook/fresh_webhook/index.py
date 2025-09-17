import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fresh_webhook.event_dispatcher import EventDispatcher

def handler(event, _):
    print("Orig Event:")
    print(json.dumps(event))
    result = EventDispatcher(event).dispatch()
    print("Result:")    
    print(json.dumps(result))
    print("--------------------------------")
    return {
        'statusCode': 200,
        'body': "Success"
    }