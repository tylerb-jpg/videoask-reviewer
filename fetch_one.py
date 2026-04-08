#!/usr/bin/env python3
import json
import subprocess
import sys

token_file = '/Users/tylerbot/credentials/videoask-token.json'
with open(token_file) as f:
    token_data = json.load(f)
access_token = token_data['access_token']
org_id = '3f29b255-68a4-45c3-9cf7-883383e01bcc'

contact_id = '42f4b787-0ad2-4586-9f02-b829535a4fb8'

question_ids = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

headers = f'Authorization: Bearer {access_token}'
org_header = f'organization-id: {org_id}'

for qname, qid in question_ids.items():
    cmd = ['curl', '-s', '-H', headers, '-H', org_header,
           f'https://api.videoask.com/questions/{qid}/answers?limit=50']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching {qname}: {result.stderr}")
        continue
    data = json.loads(result.stdout)
    # Find answer with matching contact_id
    for ans in data.get('results', []):
        if ans.get('contact_id') == contact_id:
            transcript = ans.get('transcription', '')
            print(f"{qname}: {transcript[:100]}")
            break
    else:
        print(f"{qname}: No answer found for contact {contact_id}")