#!/usr/bin/env python3
import json, subprocess, os, sys
from datetime import datetime, timezone, timedelta

# Minimal test of the script
WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'

def load_token():
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    with open(token_path) as f:
        token_data = json.load(f)
    return token_data['access_token']

def va_api(url, token):
    result = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}', url,
         '-H', f'Authorization: Bearer {token}',
         '-H', f'organization-id: {ORG_ID}'],
        capture_output=True, timeout=15
    )
    output = result.stdout
    lines = output.rsplit(b'\n', 1)
    if len(lines) == 2:
        body, status = lines
        status_code = int(status.strip())
        if status_code == 200:
            # Clean JSON
            cleaned = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b' ', body)
            return json.loads(cleaned), None
        else:
            return None, f'HTTP_{status_code}'
    return None, 'NO_STATUS'

import re

def main():
    token = load_token()
    print(f"Token loaded: {token[:20]}...")
    
    # Get contacts
    data, err = va_api(
        f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=5&status=completed',
        token
    )
    if err:
        print(f"Error: {err}")
        return
    
    contacts = data.get('results', [])
    print(f"Found {len(contacts)} completed contacts")
    
    # Load state
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    processed = set(state['processed_contacts'])
    
    # Check new
    new = []
    for c in contacts:
        cid = c['contact_id']
        if cid not in processed:
            new.append(c)
    
    print(f"New contacts: {len(new)}")
    for c in new:
        print(f"  {c['contact_id']}: {c.get('email', 'no email')} ({c.get('name', 'no name')})")
    
    if new:
        # Just get first contact's transcripts
        cid = new[0]['contact_id']
        email = new[0].get('email', '')
        
        # Check sheet for duplicates
        cmd = ['gws', 'sheets', 'spreadsheets', 'values', 'get',
               '--params', json.dumps({
                   'spreadsheetId': '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0',
                   'range': 'Backlog Reviews!J2:J100'
               })]
        env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            sheet_data = json.loads(result.stdout)
            emails = {v[0].lower().strip() for v in sheet_data.get('values', []) if v}
            if email.lower() in emails:
                print(f"Duplicate in sheet: {email}")
            else:
                print(f"Not in sheet: {email}")
        
        # Get transcripts for Q3
        qid = '4312c81f-5e50-4ee6-8ab0-0342b0cce53c'
        data2, err2 = va_api(
            f'https://api.videoask.com/questions/{qid}/answers?limit=50',
            token
        )
        if not err2:
            items = data2.get('results', [])
            for ans in items:
                if ans.get('contact_id') == cid:
                    transcript = ans.get('transcription', '')
                    print(f"Q3 transcript: {transcript[:100]}...")
                    break

if __name__ == '__main__':
    main()