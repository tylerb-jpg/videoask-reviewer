#!/usr/bin/env python3
import json, requests, sys, os
from datetime import datetime, timezone, timedelta

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'

def main():
    # Load token
    with open(f'{CREDENTIALS_DIR}/videoask-token.json') as f:
        token_data = json.load(f)
    token = token_data['access_token']
    
    # Check token expiry
    obtained = token_data.get('obtained_at', '')
    expires_in = token_data.get('expires_in', 86400)
    if obtained:
        obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
        expires_at = obtained_dt + timedelta(seconds=expires_in)
        now = datetime.now(timezone.utc)
        if expires_at < now:
            print(json.dumps({'error': 'TOKEN_EXPIRED', 'new_count': 0}))
            return
    
    # Get contacts
    headers = {
        'Authorization': f'Bearer {token}',
        'organization-id': ORG_ID
    }
    resp = requests.get(f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=100', headers=headers, timeout=10)
    if resp.status_code != 200:
        print(json.dumps({'error': f'API_FAILED_{resp.status_code}', 'new_count':270]))
        return
    
    data = resp.json()
    contacts = data.get('results', [])
    completed = [c for c in contacts if c.get('status') == 'completed']
    
    # Load processed contacts
    with open(f'{WORKSPACE}/videoask-state.json') as f:
        state = json.load(f)
    processed = set(state.get('processed_contacts', []))
    
    new_completed = [c for c in completed if c['contact_id'] not in processed]
    
    # Output just the count
    output = {
        'new_count': len(new_completed),
        'error': None
    }
    
    print(json.dumps(output))

if __name__ == '__main__':
    main()