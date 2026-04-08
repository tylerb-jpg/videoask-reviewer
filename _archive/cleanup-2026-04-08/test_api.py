#!/usr/bin/env python3
import requests, json, os, sys

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

# Get contacts
url = f'https://api.videoask.com/forms/{form_id}/contacts?limit=100&status=completed'
print(f"Requesting: {url}")
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    results = data.get('results', data.get('items', []))
    print(f"Total completed contacts: {len(results)}")
    
    # Load state
    state_path = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer/videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    
    processed = set(state['processed_contacts'])
    print(f"Already processed: {len(processed)}")
    
    new_contacts = []
    for c in results:
        cid = c['contact_id']
        if cid not in processed:
            new_contacts.append(c)
    
    print(f"New contacts: {len(new_contacts)}")
    if new_contacts:
        print("New contact IDs:")
        for c in new_contacts[:5]:
            print(f"  - {c['contact_id']} ({c.get('email') or 'no email'})")
    
    # Check sheet emails
    import subprocess
    env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
    result = subprocess.run(['gws', 'sheets', 'spreadsheets', 'get', '--params', f'{{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0"}}'], env=env, capture_output=True, text=True)
    if result.returncode == 0:
        print("Sheet accessible")
    else:
        print(f"Sheet error: {result.stderr}")
        
else:
    print(f"Error: {response.text}")