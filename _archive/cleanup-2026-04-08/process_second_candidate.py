#!/usr/bin/env python3
"""
Process a second candidate after Stephanie Price
"""
import json, requests, re, subprocess, os, sys, time
from datetime import datetime, timezone, timedelta

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_ID = 412743935
GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

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
contacts = response.json().get('results', [])

# Find next unprocessed contact (skip Stephanie)
candidate = None
for contact in contacts:
    cid = contact['contact_id']
    if cid not in processed:
        candidate = contact
        break

if not candidate:
    print("No more new candidates")
    sys.exit(0)

print(f"Found candidate: {candidate['contact_id']} - {candidate.get('name')}")

contact_id = candidate['contact_id']
name = candidate.get('name', '')
email = (candidate.get('email') or '').lower()
phone = candidate.get('phone_number', '')
va_date = candidate.get('created_at', '')

# Parse date
try:
    dt = datetime.fromisoformat(va_date.replace('Z', '+00:00'))
    va_date_str = dt.strftime('%Y-%m-%d')
except:
    va_date_str = '2026-04-06'

# Get transcripts
questions = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9'
}

transcripts = {}
for qkey, qid in questions.items():
    url = f'https://api.videoask.com/questions/{qid}/answers?limit=50'
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        answers = response.json().get('results', [])
        for ans in answers:
            if ans.get('contact_id') == contact_id:
                transcripts[qkey] = ans.get('transcription', '')
                break
        else:
            transcripts[qkey] = ''
    else:
        transcripts[qkey] = ''

# Display for analysis
print(f"\nName: {name}")
print(f"Email: {email}")
print(f"Phone: {phone}")
print(f"Date: {va_date_str}")
print()

# Count answered questions
answered = sum(1 for t in transcripts.values() if t and len(t.strip()) > 0)
print(f"Questions answered: {answered}/5")

for qkey in ['q3','q4','q5','q6','q7']:
    print(f"\n{qkey.upper()}:")
    if transcripts.get(qkey):
        print(transcripts[qkey][:300] + ("..." if len(transcripts[qkey]) > 300 else ""))
    else:
        print("(No answer)")

# Check area code
phone_market = 'unknown'
if phone:
    area = re.search(r'\((\d{3})\)', phone)
    if area:
        code = area.group(1)
        print(f"\nArea code: {code}")
        if code in ['801','385','435']:
            phone_market = 'utah'
        elif code in ['404','470','678','770','762','706','912','229','478']:
            phone_market = 'georgia'
        elif code in ['480','602','623','520','928']:
            phone_market = 'arizona'
        else:
            phone_market = 'unknown'
        print(f"Market from area code: {phone_market}")

# Now I need to write an AI summary based on this
print("\n=== NEED AI SUMMARY ===")
print("Based on the transcripts above, write a 2-3 sentence specific, opinionated assessment.")
print("Example format:")
print("- 'Keyonna has worked in multiple daycares and preschools with infants through preschool-age kids, currently pursuing an elementary education degree. In-market in south Atlanta with a reasonable drive radius.'")
print("- 'Breanna is a nursing student with years of babysitting since age 12 but no formal childcare setting. Healthcare background shows responsibility. Georgia prefers formal — judgment call for Erica.'")

# Ask for user input to write the summary
print("\nPlease provide the AI summary for this candidate:")