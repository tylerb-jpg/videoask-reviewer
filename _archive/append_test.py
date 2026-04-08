#!/usr/bin/env python3
import json, subprocess, sys, os

SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
GWS_ENV = {'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

row_data = [
    "FALSE",  # A Reviewed
    "FALSE",  # B Erica Approved
    "2026-03-31",  # C Date
    "🟢 Malaysia Robinson",  # D Name
    "GA",  # E Market
    "✅ APPROVE (MEDIUM)",  # F Rec
    '=HYPERLINK("https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/17a8343f-fd2b-4d88-a07d-07aae3759509","▶️ Watch")',  # G VideoAsk
    "Malaysia",  # H First Name
    "HFLf5aZ8HmaGb4LG7xKSfLTbDBF2",  # I App ID
    "the.malaysiajanel@gmail.com",  # J Email
    "(757) 269-1385",  # K Phone
    '=HYPERLINK("https://upkid.zendesk.com/agent/search/1?q=the.malaysiajanel%40gmail.com","🔍")',  # L Zendesk
    '=TEXT(TODAY(),"MM/DD") & " Intro Call Passed. Sandy Springs, GA, willing to travel. 10+ years teaching/coaching experience, including children with autism. Full-time availability."',  # M Zendesk Note (Approved)
    '=TEXT(TODAY(),"MM/DD") & " Not Hiring — Intro Call. Sandy Springs, GA. Phone area code mismatch (VA) raises location uncertainty."',  # N Zendesk Note (Denied)
    "10+ years teaching/coaching; autism experience",  # O Experience
    "Sandy Springs, GA",  # P Location / Drive
    "FT, open availability",  # Q Schedule
    "Malaysia has 10+ years teaching/coaching experience including work with children with autism - a valuable specialized skill. She's in-market in Sandy Springs, GA with full-time availability, but the Virginia area code needs verification (possible relocation or old number). Strong candidate if location is confirmed.",  # R Summary
    "📞 Area code = Virginia (757) but claims Georgia location — verify relocation status",  # S Red Flags
    "Hello. Hi, my name is Malaysia Robinson. I am 26 years old and I am trying to upskill I'm experience in teaching and coaching coaching children for 10-plus years.",  # T Q3 - Experience
    "I am located in Sandy Springs. Georgia, it's in between Roswell Dunwoody and Sandy Springs, and I am willing to travel.",  # U Q4 - Location
    "I am looking for full-time work and I do have open availability.",  # V Q5 - Schedule
    "First, when I noticed the conflict, I will deescalate it. At separating the children, I will ask one of the children on the stage. The child that would made look like initiated the conflict. I will sit down talk to them. Ask how they're feeling how they're doing? What made them act in such a way that they did? I'll make sure that they know that that is it right? There is other ways to go about handling conflict when maybe your feelings are hurt or maybe someone did something to you. And I just deescalate it. I'm sure that every different facility will have a chain of events or like gay steps to the escalation, I'm in my past experience, so I will do that with both of the children.",  # W Q6 - Conflict
    "So what I've noticed with my kids and I also have experience in teaching and caring for children with autism, I am pretty sure I'm about 5 feet. I do have a high pitch voice and I've been told that I look fairly young, so children feel more comfortable with me. I'm not I'm like, what the big scary adult in their words or their view. I wouldn't be that prototypical or stereotype in a child's eyes."  # X Q7 - Why Great
]

# Build JSON request
request = {
    "spreadsheetId": SPREADSHEET_ID,
    "range": "Backlog Reviews!A:X",
    "valueInputOption": "USER_ENTERED",
    "insertDataOption": "INSERT_ROWS",
    "values": [row_data]
}

cmd = [
    "gws", "sheets", "spreadsheets", "values", "append",
    "--params", json.dumps({"spreadsheetId": SPREADSHEET_ID}),
    "--json", json.dumps(request)
]

print("Running command:", ' '.join(cmd[:10]), "...")
result = subprocess.run(cmd, capture_output=True, text=True, env={**GWS_ENV, **dict(os.environ)})
print("Return code:", result.returncode)
print("Stdout:", result.stdout[:500])
if result.stderr:
    print("Stderr:", result.stderr[:500])