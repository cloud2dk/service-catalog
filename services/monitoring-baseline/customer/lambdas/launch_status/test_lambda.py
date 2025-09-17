import json
import sys
from index import handler

def invoke_lambda(event_file):
    # Load the event from the JSON file
    with open(event_file, 'r') as f:
        event = json.load(f)
    
    # Call the Lambda handler
    response = handler(event, None)
    
    # Print the response
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_lambda.py test_event.json")
        sys.exit(1)
    
    invoke_lambda(sys.argv[1]) 