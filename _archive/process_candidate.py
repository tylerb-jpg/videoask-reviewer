#!/usr/bin/env python3
import json, subprocess, os, sys

# Load candidate data from previous output
with open('/tmp/output.json', 'r') as f:
    data = json.load(f)

candidate = data['candidates'][0]  # Sharnise Ford
print(f"Processing candidate: {candidate['name']}")

# Environment for gws
env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

# Get current row count using sheets get
cmd = ['gws', 'sheets', 'spreadsheets', 'get', '--params', '{"spreadsheetId": "1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0"}']
result = subprocess.run(cmd, capture_output=True, text=True, env=env)
if result.returncode != 0:
    print(f"Error getting spreadsheet: {result.stderr}")
    sys.exit(1)

sheet_data = json.loads(result.stdout)
row_count = sheet_data['sheets'][0]['properties']['gridProperties']['rowCount']
print(f"Total rows in sheet: {row_count}")

# Count non-empty rows by checking column A
# We'll assume row 1 is header, and we need to find first empty cell
# Let's get values for column A
cmd = ['gws', 'sheets', 'spreadsheets', 'values', 'get', '--params', '{"spreadsheetId": "1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0", "range": "Backlog Reviews!A:A"}']
result = subprocess.run(cmd, capture_output=True, text=True, env=env)
if result.returncode != 0:
    print(f"Error getting values: {result.stderr}")
    sys.exit(1)

values_data = json.loads(result.stdout)
values = values_data.get('values', [])
non_empty = sum(1 for row in values if row and row[0] not in ('', None))
print(f"Non-empty rows in column A: {non_empty}")
print(f"Next row index (0-indexed): {non_empty}")
print(f"Next row number (1-indexed): {non_empty + 1}")

# Build row values according to column layout
# A: FALSE (Reviewed checkbox)
# B: FALSE (Erica Approved checkbox)
# C: va_date
# D: app_match emoji + name
# E: market (GA/UT/AZ)
# F: rec emoji (✅/🟡) + confidence
# G: =HYPERLINK("va_link", "▶️ Watch")
# H: first_name
# I: doc_id
# J: email
# K: phone_formatted
# L: =HYPERLINK("zd_link", "🔍")
# M: =TEXT(TODAY(),"MM/DD") & " Intro Call Passed. " & location + experience + schedule
# N: =TEXT(TODAY(),"MM/DD") & " Not Hiring — Intro Call. " & location + specific denial reason
# O: exp_str
# P: loc_drive
# Q: sched_str
# R: YOUR AI SUMMARY (the 2-3 sentence assessment you wrote)
# S: red_flags joined by semicolons
# T-X: transcripts q3-q7

row_values = [
    False,  # A
    False,  # B
    candidate['va_date'],  # C
    f"{candidate['app_match']} {candidate['app_name']}",  # D
    candidate['market'].upper(),  # E
    f"{'✅' if candidate['rec'] == 'APPROVE' else '🟡'} {candidate['confidence']}",  # F
    f'=HYPERLINK("{candidate["va_link"]}", "▶️ Watch")',  # G
    candidate['first_name'],  # H
    candidate['doc_id'],  # I
    candidate['email'],  # J
    candidate['phone_formatted'],  # K
    f'=HYPERLINK("{candidate["zd_link"]}", "🔍")',  # L
    f'=TEXT(TODAY(),"MM/DD") & " Intro Call Passed. {candidate["loc_drive"]}. {candidate["exp_str"]}. {candidate["sched_str"]}."',  # M
    f'=TEXT(TODAY(),"MM/DD") & " Not Hiring — Intro Call. {candidate["loc_drive"]}. No formal experience (Arizona requires 6+ months in daycare/center)."',  # N
    candidate['exp_str'],  # O
    candidate['loc_drive'],  # P
    candidate['sched_str'],  # Q
    "Sharnise has a strong formal background in early childhood, works in a daycare setting, and is CPR/first aid certified. She emphasizes safety and learning through play, and enjoys making a positive impact during children's key development stages. Solid Georgia candidate with a 25-mile drive radius, part-time availability, and straightforward conflict resolution approach.",  # R
    "; ".join(candidate['red_flags']) if candidate['red_flags'] else "",  # S
    candidate['transcripts']['q3'],  # T
    candidate['transcripts']['q4'],  # U
    candidate['transcripts']['q5'],  # V
    candidate['transcripts']['q6'],  # W
    candidate['transcripts']['q7'],  # X
]

print(f"Row values: {row_values}")
print(f"Row length: {len(row_values)}")