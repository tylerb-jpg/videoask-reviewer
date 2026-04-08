#!/usr/bin/env python3
import json, requests, sys, os, re, subprocess, time
from datetime import datetime, timezone, timedelta

# Minimal version to process just the first candidate
WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'

# Load token
token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
with open(token_path) as f:
    token_data = json.load(f)
token = token_data['access_token']

# Load state
state_path = f'{WORKSPACE}/videoask-state.json'
with open(state_path) as f:
    state = json.load(f)

processed = set(state['processed_contacts'])

# Get contacts
headers = {
    'Authorization': f'Bearer {token}',
    'organization-id': ORG_ID
}

url = f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=100&status=completed'
response = requests.get(url, headers=headers, timeout=30)
if response.status_code != 200:
    print(json.dumps({"error": f"HTTP {response.status_code}", "candidates": []}))
    sys.exit(1)

data = response.json()
all_contacts = data.get('results', [])

# Find first unprocessed contact
candidate = None
for contact in all_contacts:
    cid = contact['contact_id']
    if cid not in processed:
        candidate = contact
        break

if not candidate:
    print(json.dumps({"new_count": openings, "candidates": []}))
    sys.exit(0)

print(f"Found new candidate: {candidate['contact_id']} - {candidate.get('name')}")

# Get transcripts
transcripts = {}
for qkey, qid in [('q3', '4312c81f-5e50-4ee6-8ab0-0342b0cce53c'),
                  ('q4', 'd796e231-caac-433f-be1e-4080793da124'),
                  ('q5', 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f'),
                  ('q6', '9eedc1d8-00d0-45c1-8366-a2a34111602e'),
                  ('q7', '2f9acb14-72d1-474c-a559-be5df35d6dd9')]:
    url = f'https://api.videoask.com/questions/{qid}/answers?limit=50'
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        answers = resp.json().get('results', [])
        for ans in answers:
            if ans.get('contact_id') == candidate['contact_id']:
                transcripts[qkey] = ans.get('transcription', '')
                break
        else:
            transcripts[qkey] = ''
    else:
        transcripts[qkey] = ''

# Basic evaluation
name = candidate.get('name', '')
email = (candidate.get('email') or '').lower()
phone = candidate.get('phone_number', '')
va_date = candidate.get('created_at', '')

# Count answered questions
q_count = sum(1 for q in ['q3','q4','q5','q6','q7'] if transcripts.get(q) and len(transcripts[q]) > 10)

# Check area code
phone_market = 'unknown'
if phone:
    area = re.search(r'\((\d{3})\)', phone)
    if area:
        code = area.group(1)
        if code in ['801','385','435']:
            phone_market = 'utah'
        elif code in ['404','470','678','770','762','706','912','229','478']:
            phone_market = 'georgia'
        elif code in ['480','602','623','520','928']:
            phone_market = 'arizona'

# For now, just output basic info
output = {
    'new_count': 1,
    'candidates': [{
        'contact_id': candidate['contact_id'],
        'email': email,
        'name': name,
        'phone': phone,
        'va_date': va_date,
        'transcripts': transcripts,
        'questions_answered': q_count,
        'phone_market': phone_market
    }]
}

print(json.dumps(output, indent=2))