import boto3
import json 

session = boto3.session.Session()

def get_secret_value(secret_name):
    """Retrieve secret from AWS Secrets Manager, raising an exception on failure."""    
    client = session.client(service_name='secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)

    secret_string = response.get('SecretString')
    if secret_string:
        return json.loads(secret_string)
    else:
        raise Exception("Secret string is empty or not found in the response.")
    

# using the list-tags-for-resource API
def get_cloudwatch_alarm_tags(alarm_name):
    client = session.client(service_name='cloudwatch')
    response = client.list_tags_for_resource(ResourceARN=alarm_name)
    return response["Tags"]
