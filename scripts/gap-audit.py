#!/usr/bin/env python3
"""
Audit VideoAsk candidates across 3 sources to find gaps.
Outputs JSON: { api_total, sheet_total, state_total, matched, dropped, state_bug, sheet_junk }

Dropped = in API, not processed, not in sheet (these need attention)
State bug = marked processed but not in sheet (already handled, informational)
"""
import json, subprocess, os, sys

TOKEN_FILE = '/Users/tylerbot/credentials/videoask-token.json'
STATE_FILE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer/videoask-state.json'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_NAME = 'Backlog Reviews'
GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

# 1. VideoAsk API
with open(TOKEN_FILE) as f:
    token = json.load(f)['access_token']

api_contacts = []
offset = 0
while True:
    result = subprocess.run(
        ['curl', '-s', f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=100&offset={offset}&status=completed',
         '-H', f'Authorization: Bearer {token}',
         '-H', f'organization-id: {ORG_ID}'],
        capture_output=True, text=True, timeout=30
    )
    data = json.loads(result.stdout)
    items = data.get('results', data.get('items', []))
    api_contacts.extend(items)
    if not data.get('next') or len(items) == 0:
        break
    offset += 100

# 2. State file
with open(STATE_FILE) as f:
    state = json.load(f)
processed_ids = set(state.get('processed_contacts', []))

# 3. Sheet emails
result = subprocess.run(
    ['gws', 'sheets', 'spreadsheets', 'values', 'get',
     '--params', json.dumps({'spreadsheetId': SPREADSHEET_ID, 'range': f'{SHEET_NAME}!J2:J2000'})],
    capture_output=True, text=True, env=GWS_ENV, timeout=15
)
sheet_emails = set()
for v in json.loads(result.stdout).get('values', []):
    if v:
        sheet_emails.add(v[0].strip().lower())

# Cross-reference
dropped = []
for c in api_contacts:
    email = (c.get('email') or '').strip().lower()
    if c['contact_id'] not in processed_ids and email not in sheet_emails:
        dropped.append({'name': c.get('name', ''), 'email': email, 'contact_id': c['contact_id']})

# Find sheet row count
result2 = subprocess.run(
    ['gws', 'sheets', 'spreadsheets', 'values', 'get',
     '--params', json.dumps({'spreadsheetId': SPREADSHEET_ID, 'range': f'{SHEET_NAME}!A2:A2000', 'majorDimension': 'COLUMNS'})],
    capture_output=True, text=True, env=GWS_ENV, timeout=15
)
col_a = json.loads(result2.stdout).get('values', [[]])[0]
sheet_row_count = sum(1 for v in col_a if v and v.strip())

output = {
    'api_total': len(api_contacts),
    'sheet_rows': sheet_row_count,
    'state_processed': len(processed_ids),
    'sheet_emails': len(sheet_emails),
    'dropped': len(dropped),
    'dropped_candidates': dropped[:10],  # First 10 for Slack messages
    'healthy': len(dropped) < 5,
}
print(json.dumps(output, indent=2))
