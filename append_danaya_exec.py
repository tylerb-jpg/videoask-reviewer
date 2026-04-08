#!/usr/bin/env python3
import os
import subprocess
import json

# Set environment variable
os.environ['GOOGLE_WORKSPACE_CLI_CONFIG_DIR'] = '/Users/tylerbot/.config/gws-write'

# Build the request data
data = {
    "spreadsheetId": "1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0",
    "range": "Backlog Reviews",
    "valueInputOption": "USER_ENTERED",
    "values": [[
        False,  # A: Reviewed checkbox
        False,  # B: Erica Approved checkbox
        "2026-04-07",  # C: va_date
        "🟢 Danaya Guider",  # D: app_match emoji + name
        "georgia",  # E: market
        "🟡 MEDIUM",  # F: rec emoji + confidence
        '=HYPERLINK("https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/9076987b-4150-48cc-87e1-301b215fd402", "▶️ Watch")',  # G: videoask link
        "Danaya",  # H: first_name
        "02RDqAW2KbX4rvPmefS7nzGztLo1",  # I: doc_id
        "danayaashanti2@gmail.com",  # J: email
        "(678) 972-2809",  # K: phone_formatted
        '=HYPERLINK("https://upkid.zendesk.com/agent/search/1?q=danayaashanti2@gmail.com", "🔍")',  # L: zendesk link
        '=TEXT(TODAY(),"MM/DD") & " Intro Call Passed. Griffin, Georgia, 35mi babysitter, PT, around school"',  # M: approved note
        '=TEXT(TODAY(),"MM/DD") & " Not Hiring — Intro Call. Griffin, Georgia. Still candidate for review"',  # N: denied note
        "babysitter",  # O: exp_str
        "Griffin, Georgia, 35mi",  # P: loc_drive
        "PT, around school",  # Q: sched_str
        "Danaya has babysitting experience with ages 2-5 and is pursuing a teaching career. She lives in Griffin, GA, with a 35-minute drive radius, and is available part-time around her school schedule.",  # R: AI summary
        "",  # S: red_flags (empty)
        "",  # T: q3 transcript
        "",  # U: q4 transcript
        "",  # V: q5 transcript
        "",  # W: q6 transcript
        "",  # X: q7 transcript
    ]]
}

# Write the JSON to a temporary file
with open('/tmp/danaya_append_data.json', 'w') as f:
    json.dump(data, f)

# Build the command
cmd = [
    'gws', 'sheets', 'spreadsheets', 'values', 'append',
    '--params', '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0","range":"Backlog Reviews","valueInputOption":"USER_ENTERED"}',
    '--json', '@/tmp/danaya_append_data.json'
]

print("Executing command: " + ' '.join(cmd))

result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)