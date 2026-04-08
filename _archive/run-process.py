#!/usr/bin/env python3
import json
import subprocess
import os
import sys
import re
from datetime import datetime, timezone, timedelta

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
MDT = timezone(timedelta(hours=-6))
MAX_PER_RUN = 2

QUESTION_IDS = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

def load_token():
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    with open(token_path) as f:
        token_data = json.load(f)
    return token_data['access_token']

def load_state():
    state_path = f'{WORKSPACE}/videoask-state.json'
    if os.path.exists(state_path):
        with open(state_path) as f:
            return json.load(f)
    return {'processed_contacts': [], 'pending_match': []}

def va_api_simple(url, token):
    """Simple API call without curl status code parsing"""
    cmd = ['curl', '-s', url,
           '-H', f'Authorization: Bearer {token}',
           '-H', f'organization-id: {ORG_ID}']
    result = subprocess.run(cmd, capture_output=True, timeout=10)
    if result.returncode != 0:
        return None, f'CURL_ERROR_{result.returncode}'
    try:
        return json.loads(result.stdout), None
    except:
        return None, 'JSON_PARSE_ERROR'

def main():
    state = load_state()
    processed = set(state.get('processed_contacts', []))
    
    token = load_token()
    if not token:
        print(json.dumps({"error": "NO_TOKEN", "candidates": []}))
        return
    
    # Get completed contacts
    all_contacts = []
    offset = 0
    while True:
        data, err = va_api_simple(
            f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=20&offset={offset}&status=completed',
            token
        )
        if err:
            print(json.dumps({"error": err, "candidates": []}))
            return
        items = data.get('results', data.get('items', []))
        all_contacts.extend(items)
        if not data.get('next') or len(items) == 0:
            break
        offset += 20
        if offset > 40:  # Limit to first page for speed
            break
    
    # Filter to new
    new_contacts = [c for c in all_contacts if c['contact_id'] not in processed]
    if not new_contacts:
        print(json.dumps({"new_count": 0, "candidates": []}))
        return
    
    # Rate limit
    new_contacts = new_contacts[:MAX_PER_RUN]
    
    # Process each
    candidates = []
    for contact in new_contacts:
        cid = contact['contact_id']
        email = (contact.get('email') or '').strip()
        phone = (contact.get('phone_number') or '').strip()
        name = (contact.get('name') or '').strip()
        
        # Pull transcripts for Q3-Q7
        transcripts = {}
        for qkey, qid in QUESTION_IDS.items():
            data, err = va_api_simple(
                f'https://api.videoask.com/questions/{qid}/answers?limit=20',
                token
            )
            if err:
                continue
            items = data.get('results', data.get('items', []))
            for ans in items:
                if ans.get('contact_id') == cid:
                    t = ans.get('transcription', '')
                    if t and t.strip():
                        transcripts[qkey] = t.strip()
                    break
        
        q_count = sum(1 for q in ['q3','q4','q5','q6','q7'] if transcripts.get(q))
        
        # Simple candidate object
        candidate = {
            'contact_id': cid,
            'name': name,
            'email': email,
            'phone': phone,
            'questions_answered': q_count,
            'transcripts': transcripts,
        }
        candidates.append(candidate)
    
    output = {
        'new_count': len(candidates),
        'total_checked': len(all_contacts),
        'candidates': candidates,
    }
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()