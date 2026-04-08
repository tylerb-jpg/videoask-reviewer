#!/usr/bin/env python3
import os
import subprocess
import json

# Set environment variable
os.environ['GOOGLE_WORKSPACE_CLI_CONFIG_DIR'] = '/Users/tylerbot/.config/gws-write'

# Try to append a full row
cmd = [
    'gws', 'sheets', 'spreadsheets', 'values', 'append',
    '--params', '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0","range":"Backlog Reviews!A1:X1","valueInputOption":"USER_ENTERED"}',
    '--json', '{"values":[[false, false, "2026-04-07", "🟢 Danaya Guider", "georgia", "🟡 MEDIUM", "=HYPERLINK(\\"https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/9076987b-4150-48cc-87e1-301b215fd402\\", \\"▶️ Watch\\")", "Danaya", "02RDqAW2KbX4rvPmefS7nzGztLo1", "danayaashanti2@gmail.com", "(678) 972-2809", "=HYPERLINK(\\"https://upkid.zendesk.com/agent/search/1?q=danayaashanti2@gmail.com\\", \\"🔍\\")", "=TEXT(TODAY(),\\"MM/DD\\") & \\" Intro Call Passed. Griffin, Georgia, 35mi babysitter, PT, around school\\"", "=TEXT(TODAY(),\\"MM/DD\\") & \\" Not Hiring — Intro Call. Griffin, Georgia. Still candidate for review\\", "babysitter", "Griffin, Georgia, 35mi", "PT, around school", "Danaya has babysitting experience with ages 2-5 and is pursuing a teaching career. She lives in Griffin, GA, with a 35-minute drive radius, and is available part-time around her school schedule.", "", "", "", "", "", ""]]}'
]

print("Executing command: " + ' '.join(cmd))

result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)