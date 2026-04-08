#!/usr/bin/env python3
"""
Simplified version for cron job - fetch new submissions and output JSON.
"""
import json, os, sys, re, subprocess
from datetime import datetime, timezone, timedelta

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
MAX_PER_RUN = 2

QUESTION_IDS = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

def load_token():
    """Load VideoAsk token."""
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    with open(token_path) as f:
        token_data = json.load(f)
    # Check if expired
    obtained = token_data.get('obtained_at', '')
    expires_in = token_data.get('expires_in', 86400)
    if obtained:
        obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
        expires_dt = obtained_dt + timedelta(seconds=expires_in - 300)
        if datetime.now(timezone.utc) > expires_dt:
            print("TOKEN_EXPIRED", file=sys.stderr)
            return None
    return token_data['access_token']

def api_request(endpoint):
    """Make API request."""
    token = load_token()
    if token is None:
        return None
    cmd = ['curl', '-s', '-w', '\n%{http_code}', 
           f'https://api.videoask.com/{endpoint}',
           '-H', f'Authorization: Bearer {token}',
           '-H', f'organization-id: {ORG_ID}']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    lines = result.stdout.strip().split('\n')
    if len(lines) < 2:
        return None
    body = '\n'.join(lines[:-1])
    status = lines[-1]
    if status != '200':
        return None
    try:
        return json.loads(body)
    except:
        return None

def main():
    # Load state
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    processed = set(state.get('processed_contacts', []))
    
    # Get contacts
    data = api_request(f'forms/{FORM_ID}/contacts?limit=50')
    if data is None:
        print(json.dumps({"error": "API_ERROR", "candidates": []}))
        return
    
    contacts = data.get('results', [])
    # Filter completed, not processed
    new_contacts = []
    for c in contacts:
        if c.get('status') == 'completed' and c.get('contact_id') not in processed:
            new_contacts.append(c)
            if len(new_contacts) >= MAX_PER_RUN:
                break
    
    if not new_contacts:
        print(json.dumps({"new_count": 0, "candidates": []}))
        return
    
    # Process each
    candidates = []
    for c in new_contacts:
        cid = c['contact_id']
        
        # Get transcripts from answers
        transcripts = {}
        name, email, phone = '', '', ''
        for qname, qid in QUESTION_IDS.items():
            data = api_request(f'questions/{qid}/answers?limit=50')
            if data:
                answers = data.get('results', [])
                matching = [a for a in answers if a.get('contact_id') == cid]
                if matching:
                    a = matching[0]
                    transcripts[qname] = a.get('transcription', '')
                    # Get contact info from first answer found
                    if not name:
                        name = a.get('contact_name', '')
                        email = a.get('contact_email', '')
                        phone = a.get('contact_phone_number', '')
        
        # If no answers found, try contact endpoint
        if not name:
            data = api_request(f'contacts/{cid}')
            if data:
                name = data.get('contact_name', '')
                email = data.get('contact_email', '')
                phone = data.get('contact_phone_number', '')
        
        candidates.append({
            'contact_id': cid,
            'name': name,
            'email': email,
            'phone': phone,
            'market': 'unknown',  # Will be determined later
            'rec': 'FLAG',  # Default
            'confidence': 'LOW',
            'transcripts': transcripts,
            'questions_answered': sum(1 for t in transcripts.values() if t.strip()),
            'first_name': name.split()[0] if name else '',
        })
    
    print(json.dumps({
        'new_count': len(new_contacts),
        'candidates': candidates
    }, indent=2))

if __name__ == '__main__':
    main()