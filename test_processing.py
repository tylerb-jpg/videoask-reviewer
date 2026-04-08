#!/usr/bin/env python3
import json, requests, sys, os, subprocess, re, time
from datetime import datetime, timezone, timedelta

# Copy just the essential functions from the real script
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
    headers = {
        'Authorization': f'Bearer {token}',
        'organization-id': ORG_ID
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return None, str(e)

def main():
    token = load_token()
    if not token:
        print(json.dumps({"error": "TOKEN_EXPIRED", "candidates": []}))
        return
    
    # Get contacts
    all_contacts = []
    offset = 0
    while True:
        data, err = va_api(
            f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=100&offset={offset}&status=completed',
            token
        )
        if err:
            print(json.dumps({"error": err, "candidates": []}))
            return
        items = data.get('results', data.get('items', []))
        all_contacts.extend(items)
        if not data.get('next') or len(items) == 0:
            break
        offset += 100
    
    # Load state
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    
    processed = set(state['processed_contacts'])
    
    # Filter new contacts
    new_contacts = []
    for c in all_contacts:
        cid = c['contact_id']
        if cid not in processed:
            new_contacts.append(c)
    
    print(f"Total contacts: {len(all_contacts)}")
    print(f"Processed: {len(processed)}")
    print(f"New contacts: {len(new_contacts)}")
    
    # Limit to 2 per run
    MAX_PER_RUN = 2
    new_contacts = new_contacts[:MAX_PER_RUN]
    
    if not new_contacts:
        print(json.dumps({"new_count": 0, "candidates": []}))
        return
    
    print(f"Processing {len(new_contacts)} new candidates")
    
    # For each candidate, get transcripts
    candidates = []
    for contact in new_contacts:
        contact_id = contact['contact_id']
        email = (contact.get('email') or '').strip().lower()
        name = contact.get('name', '')
        phone = contact.get('phone_number', '')
        
        # Get answers for Q3-Q7
        transcripts = {}
        for qkey, qid in [('q3', '4312c81f-5e50-4ee6-8ab0-0342b0cce53c'),
                         ('q4', 'd796e231-caac-433f-be1e-4080793da124'),
                         ('q5', 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f'),
                         ('q6', '9eedc1d8-00d0-45c1-8366-a2a34111602e'),
                         ('q7', '2f9acb14-72d1-474c-a559-be5df35d6dd9')]:
            url = f'https://api.videoask.com/questions/{qid}/answers?limit=50&contact_id={contact_id}'
            data, err = va_api(url, token)
            if err:
                transcripts[qkey] = ''
                continue
            items = data.get('results', data.get('items', []))
            if items:
                # Find the answer for this contact
                for ans in items:
                    if ans.get('contact_id') == contact_id:
                        transcripts[qkey] = ans.get('transcription', '')
                        break
                else:
                    transcripts[qkey] = ''
            else:
                transcripts[qkey] = ''
        
        candidate = {
            'contact_id': contact_id,
            'email': email,
            'name': name,
            'phone': phone,
            'transcripts': transcripts,
            'va_date': contact.get('created_at', '')
        }
        candidates.append(candidate)
    
    output = {
        'new_count': len(new_contacts),
        'candidates': candidates
    }
    print(json.dumps(output))

if __name__ == '__main__':
    main()