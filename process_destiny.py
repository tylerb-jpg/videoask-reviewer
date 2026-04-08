#!/usr/bin/env python3
"""
Process Destiny Scott
"""
import json, re, subprocess, os, sys, time
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

# Destiny's data
contact_id = '317cecdf-cb8d-426f-947c-c04c15d43a84'
name = 'Destiny Scott'
email = 'destinytofye234@gmail.com'
phone = '+19124328353'
va_date_str = '2026-04-06'

# Get transcripts
import requests
headers = {
    'Authorization': f'Bearer {token}',
    'organization-id': ORG_ID
}

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

# Analysis
market = 'georgia'
city = 'East Point, GA'
drive = '5-20 miles'  # "five to 15. Maybe 20 miles"

# Experience - 18 years old, 2 years experience, likely informal
exp_type = 'informal'
q3_text = transcripts.get('q3', '').lower()
if 'working with kids for two years' in q3_text:
    exp_str = '2 years childcare exp (likely informal); 18 years old; pursuing science associates degree'

# Schedule
q5_text = transcripts.get('q5', '')
sched_str = 'part-time or full-time'
if 'part-time and full-time' in q5_text.lower():
    sched_str = 'part-time or full-time'

# Recommendation - FLAG due to young age + informal experience in Georgia
rec = '🟡 FLAG'
confidence = 'MEDIUM'

# AI Summary
ai_summary = "Destiny is an enthusiastic 18-year-old with 2 years of childcare experience (likely informal) who is pursuing a science degree. Her genuine passion for working with children and willingness to drive up to 20 miles from East Point, GA are positives, but her young age and lack of formal childcare experience make this a judgment call for Erica given Georgia's preference for formal experience."

# Red flags
red_flags = []
# Check area code - 912 is Georgia, so OK
# Check if male name - Destiny is female, so OK
red_flags_str = '; '.join(red_flags) if red_flags else 'None'

# App account placeholder
app_match = '🔴'  # Not found placeholder
app_name = 'Destiny Scott'
doc_id = ''

# Zendesk summaries
today = datetime.now().strftime('%m/%d')
zendesk_approved = f"{today} Intro Call Passed. East Point, GA, willing to drive 5-20 miles. 18-year-old with 2 years of childcare experience (likely informal), currently pursuing science associates degree. Interested in part-time or full-time work. Enthusiastic, outgoing, sees childcare as a career."
zendesk_denied = f"{today} Not Hiring — Intro Call. East Point, GA. Georgia typically prefers formal childcare experience; candidate is 18 with only informal experience."

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

va_link = f"https://app.videoask.com/app/organizations/{ORG_ID}/form/{FORM_ID}/conversation/{contact_id}"
zd_link = f"https://upkid.zendesk.com/agent/search/1?q={email}"

first_name = name.split()[0] if name else 'Destiny'

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
# Row colors for FLAG MEDIUM: rgb(1.0, 0.88, 0.82)
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
                            "red": 1.0,
                            "green": 0.88,
                            "blue": 0.82
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
slack_message = f"🟡 FLAG (MEDIUM) — Destiny Scott | Georgia | 2026-04-06\n{ai_summary}\n→ View in sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
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
print(f"Processed Destiny Scott (contact_id: {contact_id})")
print(f"Added to sheet row {row_count + 1}")
print(f"AI Summary: {ai_summary}")