#!/usr/bin/env python3
import json
import subprocess
import os
import sys

# Load token
token_path = '/Users/tylerbot/credentials/videoask-token.json'
with open(token_path) as f:
    token_data = json.load(f)
token = token_data['access_token']
org_id = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
form_id = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'

# Make API call
print("Testing VideoAsk API...")
cmd = ['curl', '-s', 
       f'https://api.videoask.com/forms/{form_id}/contacts?limit=5&status=completed',
       '-H', f'Authorization: Bearer {token}',
       '-H', f'organization-id: {org_id}']
result = subprocess.run(cmd, capture_output=True, timeout=10)
if result.returncode != 0:
    print(f"Error: {result.stderr}")
    sys.exit(1)

try:
    data = json.loads(result.stdout)
    contacts = data.get('results', [])
    print(f"Found {len(contacts)} completed contacts")
    
    # Load state
    state_path = 'videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    processed = set(state.get('processed_contacts', []))
    
    new_contacts = [c for c in contacts if c['contact_id'] not in processed]
    print(f"New contacts (not in processed list): {len(new_contacts)}")
    
    for c in new_contacts[:3]:
        print(f"  - {c.get('name', 'No name')} ({c['contact_id']})")
        
    if not new_contacts:
        print("No new submissions to process")
        print(json.dumps({"new_count": 0, "candidates": []}))
    else:
        print(f"Would process up to 2 of {len(new_contacts)} new contacts")
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    print(f"Response: {result.stdout[:200]}")