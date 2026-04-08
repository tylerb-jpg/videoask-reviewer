#!/usr/bin/env python3
import json, requests, sys

token_path = '/Users/tylerbot/credentials/videoask-token.json'
with open(token_path) as f:
    token_data = json.load(f)

token = token_data['access_token']
org_id = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
form_id = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'

headers = {
    'Authorization': f'Bearer {token}',
    'organization-id': org_id
}

# Simple test: get one contact
url = f'https://api.videoask.com/forms/{form_id}/contacts?limit=1&status=completed'
print(f"Testing: {url}")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Contact ID: {data['results'][0]['contact_id']}")
        print(f"Name: {data['results'][0].get('name')}")
        print(f"Email: {data['results'][0].get('email')}")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

# Test answer endpoint
print("\nTesting answers endpoint...")
qid = '4312c81f-5e50-4ee6-8ab0-0342b0cce53c'
contact_id = '79f62ce9-b5ab-4045-9c52-e27d3d4c66a1'  # From earlier test
url = f'https://api.videoask.com/questions/{qid}/answers?limit=50'
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total answers: {len(data.get('results', []))}")
        # Filter by contact_id
        for ans in data.get('results', []):
            if ans.get('contact_id') == contact_id:
                print(f"Found answer for contact {contact_id}")
                print(f"Transcript: {ans.get('transcription', '')[:200]}")
                break
        else:
            print(f"No answer found for contact {contact_id}")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")