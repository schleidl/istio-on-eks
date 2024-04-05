import boto3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler


def check_authorization(event) -> dict: 
    client = boto3.client('verifiedpermissions')

    print("event", event)

    response = client.is_authorized(
    policyStoreId='AQ4pnW9boA7iJa6EEcNxL3',
    principal={
        'entityType': 'User',
        'entityId': 'alice'
    },
    action={
        'actionType': 'Action',
        'actionId': 'ReadList'
    },
    resource={
        'entityType': 'List',
        'entityId': 'LIST#000001'
    },
    entities=event
)
    print(response.get("decision"))
    return response.get("decision")

def lambda_handler(event, context):
  decision = check_authorization(event=event)
  print("Decision right before return", decision)
  return {
    'statusCode': 200,
    'decision': decision
  }

  

  









