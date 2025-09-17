import json

def load_event(event_path):
    with open(event_path, 'r') as file:
        return json.load(file) 