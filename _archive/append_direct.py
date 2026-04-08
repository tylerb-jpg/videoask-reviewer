#!/usr/bin/env python3
import json, os, subprocess, sys

# Set environment
env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

# Build the JSON data
data = {
    "values": [
        [
            "FALSE",
            "FALSE",
            "2026-04-06",
            "🔴 Not found",
            "GA",
            "✅ HIGH",
            "=HYPERLINK(\"https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/17a8343f-fd2b-4d88-a07d-07aae3759509\", \"▶️ Watch\")",
            "Malaysia",
            "",
            "the.malaysiajanel@gmail.com",
            "(757) 269-1385",
            "=HYPERLINK(\"https://upkid.zendesk.com/agent/search/1?q=the.malaysiajanel%40gmail.com\", \"🔍\")",
            "=TEXT(TODAY(),\"MM/DD\") & \" Intro Call Passed. \" & \"Sandy Springs, GA, willing to travel. 10+ years teaching and coaching children. Full-time, open availability.\"",
            "=TEXT(TODAY(),\"MM/DD\") & \" Not Hiring — Intro Call. \" & \"Sandy Springs, GA — Virginia area code mismatch needs verification.\"",
            "Formal childcare experience",
            "Sandy Springs, GA, willing to travel",
            "Full-time, open availability",
            "Malaysia has 10+ years of teaching and coaching experience with children, showing strong formal background. She's located in Sandy Springs, Georgia (in-market) with open availability for full-time work. The Virginia area code is a minor flag but she's clearly in Georgia. Strong candidate for approval.",
            "📞 Area code = Virginia",
            "Hello. Hi, my name is Malaysia Robinson. I am 26 years old and I am trying to upskill I'm experience in teaching and coaching coaching children for 10-plus years.",
            "I am located in Sandy Springs. Georgia, it's in between Roswell Dunwoody and Sandy Springs, and I am willing to travel.",
            "I am looking for full-time work and I do have open availability.",
            "First, when I noticed the conflict, I will deescalate it. At separating the children, I will ask one of the children on the stage. The child that would made look like initiated the conflict. I will sit down talk to them. Ask how they're feeling how they're doing? What made them act in such a way that they did? I'll make sure that they know that that is it right? There is other ways to go about handling conflict when maybe your feelings are hurt or maybe someone did something to you. And I just deescalate it. I'm sure that every different facility will have a chain of events or like gay steps to the escalation, I'm in my past experience, so I will do that with both of the children.",
            ""
        ]
    ]
}

# Write to temp file
with open('/tmp/append_data.json', 'w') as f:
    json.dump(data, f)

# Run command
cmd = [
    'gws', 'sheets', 'spreadsheets', 'values', 'append',
    '--params', '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0", "range":"Backlog Reviews!A314", "valueInputOption":"USER_ENTERED"}',
    '--json', '@/tmp/append_data.json'
]

print('Running command...')
result = subprocess.run(cmd, env=env, capture_output=True, text=True)
print('stdout:', result.stdout)
print('stderr:', result.stderr)
print('returncode:', result.returncode)

if result.returncode == 0:
    print('Success!')
else:
    print('Failed. Trying alternative approach...')
    # Try simpler command
    simple_cmd = ' '.join(['GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/Users/tylerbot/.config/gws-write'] + cmd)
    print('Alternative command:', simple_cmd)