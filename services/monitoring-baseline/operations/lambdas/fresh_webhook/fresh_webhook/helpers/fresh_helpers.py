import requests

def send_event(event, secret, headers=None):
    """Send event to Fresh Webhook endpoint."""
    if headers is None:
        headers = {
            'Authorization': secret['auth_key'],
            'Content-Type': 'application/json'
        }
    else:
        # Ensure Authorization header is set
        headers['Authorization'] = secret['auth_key']
    
    endpoint = secret['endpoint']
    response = requests.post(endpoint, headers=headers, data=event)
    print(response.text)
    return response.text
    