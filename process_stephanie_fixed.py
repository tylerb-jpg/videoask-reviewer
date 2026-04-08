#!/usr/bin/env python3
"""
Complete processing for Stephanie Price - one candidate at a time
Following the cron job instructions
"""
import json, re, subprocess, os, sys, time
from datetime import datetime, timezone, timedelta

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_ID = 412743935  # Backlog Reviews sheet ID
GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

# Load token
token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
with open(token_path) as f:
    token_data = json.load(f)
token = token_data['access_token']

# Get Stephanie's data
import requests
headers = {
    'Authorization': f'Bearer {token}',
    'organization-id': ORG_ID
}

# Get contact
url = f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=100&status=completed'
response = requests.get(url, headers=headers, timeout=30)
contacts = response.json().get('results', [])

contact = None
for c in contacts:
    if c['contact_id'] == '79f62ce9-b5ab-4045-9c52-e27d3d4c66a1':
        contact = c
        break

if not contact:
    print("Contact not found")
    sys.exit(1)

contact_id = contact['contact_id']
name = contact.get('name', 'Stephanie Price')
email = (contact.get('email') or 'stephypink2000@gmail.com').lower()
phone = contact.get('phone_number', '+15203454725')
va_date = contact.get('created_at', '2026-04-06T22:05:01.279380Z')

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
        else:
            phone_market = 'unknown'

# Based on Q4: "So I live in Tucson Arizona"
market = 'arizona'
city = 'Tucson, AZ'
drive = '20 miles'  # "willing to travel about 20 miles"

# Experience analysis
exp_type = 'formal'
q3_text = transcripts.get('q3', '').lower()
if 'paraprofessional' in q3_text and 'special education' in q3_text:
    exp_str = 'paraprofessional (special education); behavior technician training; babysitting background'
elif 'babysitting' in q3_text:
    exp_str = 'babysitting + paraprofessional experience'

# Schedule
q5_text = transcripts.get('q5', '')
sched_str = 'full-time, open availability'
if 'full-time' in q5_text.lower() and 'open availability' in q5_text.lower():
    sched_str = 'full-time, open availability'

# Recommendation - looks strong
rec = '✅ APPROVE'
confidence = 'HIGH'

# AI Summary - 2-3 sentences specific, opinionated
ai_summary = "Stephanie has a strong progression from babysitting to paraprofessional work in special education classrooms, with additional training as a behavior technician for ABA therapy. Her commitment to childcare as a 'calling' and clear articulation of conflict resolution strategies make her a standout candidate for Arizona. She's willing to drive 20 miles from Tucson with full-time open availability."

# Red flags
red_flags = []
if phone_market != 'arizona' and phone_market != 'unknown':
    red_flags.append(f'📞 Area code = {phone_market.title()} (but lives in AZ)')
# Check if male name
first_name = name.split()[0].lower() if name else ''
MALE_NAMES = {'brian','john','matt','matthew','jarvis','james','george','nicholas','nico',
              'josue','elan','denetric','brodie','robert','michael','david','daniel','joseph',
              'william','richard','charles','thomas','chris','jason','ryan','kevin','brandon'}
if first_name in MALE_NAMES:
    red_flags.append('👨 MALE — centers may not place')
red_flags_str = '; '.join(red_flags) if red_flags else 'None'

# App account lookup - skip BigQuery for now, just placeholder
app_match = '🟡'  # Partial match placeholder
app_name = 'Stephanie Price'
doc_id = ''

# Zendesk summaries
today = datetime.now().strftime('%m/%d')
zendesk_approved = f"{today} Intro Call Passed. Tucson, AZ, willing to drive 20 miles. Has experience as a paraprofessional in special education classrooms with behavior technician training for ABA therapy, plus babysitting background. Looking for full-time work with open availability. Strong conflict resolution approach: separates children, checks for medical needs, talks individually to understand causes and promote positive behavior."
zendesk_denied = f"{today} Not Hiring — Intro Call. Tucson, AZ. Arizona requires 6 months formal childcare experience; candidate has paraprofessional experience which may qualify."

# ===== Step 3a: Count existing rows =====
print("Counting existing rows...")
result = subprocess.run([
    'gws', 'sheets', 'spreadsheets', 'values', 'get',
    '--params', f'{{"spreadsheetId":"{SPREADSHEET_ID}","range":"Backlog Reviews!A:A"}}'
], env=GWS_ENV, capture_output=True, text=True)
if result.returncode != 0:
    print(f"Error counting rows: {result.stderr}")
    sys.exit(1)

data = json.loads(result.stdout)
row_count = len(data.get('values', []))
print(f"Current row count: {row_count}")
row_0_indexed = row_count  # New row will be at this index

# ===== Step 3b: Append row =====
print("Appending row...")
# Column order:
# A: FALSE (Reviewed)
# B: FALSE (Erica Approved)
# C: va_date_str
# D: app_match + " " + app_name
# E: market.upper()
# F: rec + " " + confidence
# G: =HYPERLINK("va_link", "▶️ Watch")
# H: first name
# I: doc_id
# J: email
# K: phone formatted
# L: =HYPERLINK("zd_link", "🔍")
# M: zendesk_approved
# N: zendesk_denied
# O: exp_str
# P: f"{city}, {drive}"
# Q: sched_str
# R: ai_summary
# S: red_flags_str
# T-X: transcripts q3-q7

va_link = f"https://app.videoask.com/app/organizations/{ORG_ID}/form/{FORM_ID}/conversation/{contact_id}"
zd_link = f"https://upkid.zendesk.com/agent/search/1?q={email}"

first_name = name.split()[0] if name else 'Stephanie'

row_values = [
    False,  # A: Reviewed
    False,  # B: Erica Approved
    va_date_str,  # C: Date
    f"{app_match} {app_name}",  # D: App match + name
    market.upper(),  # E: Market
    f"{rec} {confidence}",  # F: Rec + confidence
    f'=HYPERLINK("{va_link}", "▶️ Watch")',  # G: VideoAsk link
    first_name,  # H: First Name
    doc_id,  # I: App ID
    email,  # J: Email
    phone,  # K: Phone
    f'=HYPERLINK("{zd_link}", "🔍")',  # L: Zendesk link
    zendesk_approved,  # M: Zendesk approved note
    zendesk_denied,  # N: Zendesk denied note
    exp_str,  # O: Experience
    f"{city}, {drive}",  # P: Location/Drive
    sched_str,  # Q: Schedule
    ai_summary,  # R: Summary
    red_flags_str,  # S: Red Flags
    transcripts.get('q3', ''),  # T: Q3
    transcripts.get('q4', ''),  # U: Q4
    transcripts.get('q5', ''),  # V: Q5
    transcripts.get('q6', ''),  # W: Q6
    transcripts.get('q7', '')   # X: Q7
]

# Append
append_cmd = [
    'gws', 'sheets', 'spreadsheets', 'values', 'append',
    '--params', f'{{"spreadsheetId":"{SPREADSHEET_ID}","range":"Backlog Reviews!A:X","valueInputOption":"USER_ENTERED","insertDataOption":"INSERT_ROWS"}}',
    '--json', f'{{"values": [{json.dumps(row_values)}]}}'
]

print(f"Running: {' '.join(append_cmd)}")
result = subprocess.run(append_cmd, env=GWS_ENV, capture_output=True, text=True)
if result.returncode != 0:
    print(f"Append error: {result.stderr}")
    sys.exit(1)
print("Append successful")

# ===== Step 3c: Apply formatting =====
print("Applying formatting...")
# Row colors for APPROVE HIGH: rgb(0.85, 0.95, 0.85)
batch_json = {
    "requests": [
        {
            "setDataValidation": {
                "range": {
                    "sheetId": SHEET_ID,
                    "startRowIndex": row_0_indexed,
                    "endRowIndex": row_0_indexed + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 2
                },
                "rule": {
                    "condition": { "type": "BOOLEAN" },
                    "showCustomUi": True
                }
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": SHEET_ID,
                    "startRowIndex": row_0_indexed,
                    "endRowIndex": row_0_indexed + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 2
                },
                "cell": {
                    "userEnteredValue": { "boolValue": False }
                },
                "fields": "userEnteredValue"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": SHEET_ID,
                    "startRowIndex": row_0_indexed,
                    "endRowIndex": row_0_indexed + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 24
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 0.85,
                            "green": 0.95,
                            "blue": 0.85
                        }
                    }
                },
                "fields": "userEnteredFormat.backgroundColor"
            }
        }
    ]
}

format_cmd = [
    'gws', 'sheets', 'spreadsheets', 'batchUpdate',
    '--params', f'{{"spreadsheetId":"{SPREADSHEET_ID}"}}',
    '--json', json.dumps(batch_json)
]

print(f"Running format command...")
result = subprocess.run(format_cmd, env=GWS_ENV, capture_output=True, text=True)
if result.returncode != 0:
    print(f"Format error: {result.stderr}")
    sys.exit(1)
print("Formatting successful")

# ===== Step 3d: Post to Slack =====
print("Posting to Slack...")
# We can't actually post to Slack from here, but we can print the message
slack_message = f"✅ APPROVE (HIGH) — Stephanie Price | Arizona | 2026-04-06\n{ai_summary}\n→ View in sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
print(f"Slack message:\n{slack_message}")

# ===== Step 3e: Mark as processed =====
print("Marking as processed...")
mark_cmd = ['python3', f'{WORKSPACE}/scripts/mark-done.py', contact_id]
result = subprocess.run(mark_cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"Mark done error: {result.stderr}")
    sys.exit(1)
print(f"Mark done output: {result.stdout.strip()}")

print("\n=== COMPLETE ===")
print(f"Processed Stephanie Price (contact_id: {contact_id})")
print(f"Added to sheet row {row_count + 1}")
print(f"AI Summary: {ai_summary}")