#!/usr/bin/env python3
import json, subprocess, sys, os
from datetime import datetime, timezone, timedelta

def load_token():
    token_path = '/Users/tylerbot/credentials/videoask-token.json'
    with open(token_path) as f:
        data = json.load(f)
    obtained = data.get('obtained_at', '')
    expires_in = data.get('expires_in', 86400)
    if obtained:
        obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
        expires_dt = obtained_dt + timedelta(seconds=expires_in - 300)
        if datetime.now(timezone.utc) > expires_dt:
            print("TOKEN_EXPIRED")
            sys.exit(1)
    return data['access_token']

token = load_token()
org = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
form = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'

# Fetch contacts
headers = f'Authorization: Bearer {token}'
org_header = f'organization-id: {org}'
url = f'https://api.videoask.com/forms/{form}/contacts?limit=20'
cmd = ['curl', '-s', '-H', headers, '-H', org_header, url]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if result.returncode != 0:
    print('curl error', file=sys.stderr)
    sys.exit(1)
data = json.loads(result.stdout)
contacts = data.get('results', [])

# Load processed state
state_path = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer/videoask-state.json'
with open(state_path) as f:
    state = json.load(f)
processed = set(state['processed_contacts'])

# Find new completed contacts
new = []
for c in contacts:
    if c['status'] == 'completed' and c['contact_id'] not in processed:
        new.append(c)

print(f'Found {len(new)} new completed contacts', file=sys.stderr)

if not new:
    print('{"new_count": 0, "new_candidates": []}')
    sys.exit(0)

# Process first candidate only (for now)
candidate = new[0]
contact_id = candidate['contact_id']

# Fetch all answers for each question once
question_ids = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

transcripts = {}
for qname, qid in question_ids.items():
    url = f'https://api.videoask.com/questions/{qid}/answers?limit=50'
    cmd = ['curl', '-s', '-H', headers, '-H', org_header, url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        ans_data = json.loads(result.stdout)
        for ans in ans_data.get('results', []):
            if ans.get('contact_id') == contact_id:
                transcripts[qname] = ans.get('transcription', '')
                break
        else:
            transcripts[qname] = ''
    else:
        transcripts[qname] = ''

output = {
    'new_count': len(new),
    'new_candidates': [{
        'contact_id': contact_id,
        'created_at': candidate['created_at'],
        'contact_email': candidate.get('email'),
        'contact_name': candidate.get('name'),
        'status': candidate['status'],
        'transcripts': transcripts
    }]
}

print(json.dumps(output, indent=2))