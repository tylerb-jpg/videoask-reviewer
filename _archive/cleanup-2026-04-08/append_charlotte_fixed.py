#!/usr/bin/env python3
import json
import subprocess
import os

# Charlotte's data
charlotte_data = {
    "contact_id": "b38a00a4-f032-43ea-8eb4-0a97c10e0e28",
    "name": "Charlotte Howard",
    "email": "charlottehoward2025@gmail.com",
    "phone": "+14703151897",
    "phone_formatted": "(470) 315-1897",
    "market": "georgia",
    "va_date": "2026-04-07",
    "rec": "APPROVE",
    "confidence": "MEDIUM",
    "exp_type": "mixed",
    "exp_str": "daycare; babysitter; nursing bg",
    "city": "Kennesaw, GA",
    "drive": "30mi",
    "loc_drive": "Kennesaw, GA, 30mi",
    "sched_str": "FT, PT",
    "questions_answered": 5,
    "app_match": "🟢",
    "app_name": "Charlotte Howard",
    "doc_id": "EVCx40n3VRMokbjUXKnPlvydUAG3",
    "red_flags": [],
    "va_link": "https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/b38a00a4-f032-43ea-8eb4-0a97c10e0e28",
    "zd_link": "https://upkid.zendesk.com/agent/search/1?q=charlottehoward2025@gmail.com",
    "summary": "Charlotte has strong mixed experience with daycare work and nursing background showing responsibility. Her conflict resolution answer demonstrates maturity and she comes across as genuine and passionate about working with kids. Only missing is a stated drive radius but the Kennesaw area should have good Upkid coverage.",
    "transcripts": {
        "q3": "Hey somebody was Charlotte Howard and I'm a college student at Kennesaw State University and I work with all ages especially like having a background in child care. Like since I was like 16 I guess we worked a lot of daycares like Sunshine House kids are kids and things like that I don't know all age groups and in college like since I've started off this would be babysitting. So I hope I fall experience with age.\n Just like all ranges of Ages and things like that. And I'm a nursing major also to do pediatrics. So I'm always like around kids or their it's internships or just babysitting and I just love working with kids and have a passion for it, so yeah.",
        "q4": "Okay, so I'm located in Kennesaw Georgia and I think I probably would have to travel at most like 25 or 30 minutes and yeah.",
        "q5": "I'm a very flexible schedule. So I think like full-time would probably be better, but I could make part-time or anything. But I think full-time would definitely be like my prefer schedule at the moment.",
        "q6": "And dealing with conflict, which road and I try to like be very gentle and of two children, and one hit another hour, probably like just break it up and make the other kid apologized and make them. Like, just go sit and talk about to calm down for a bit and then, you know, just let them call me out for a bit and eventually everything will just go back to normal, but I would definitely make them apologize to each other and just take some time to cool down.",
        "q7": "I think I'll make a great up K teacher because first are very reliable when, you know, always on time very like punctual and I'm very friendly, I have experience with kids already, which is a plus. And I definitely just think that I would just fit the company and, you know, just be a good help. So yeah, I've experienced very nice with kids and reliable."
    }
}

# Build the row data
row_data = [
    "FALSE",  # A - Reviewed checkbox
    "FALSE",  # B - Erica Approved checkbox
    charlotte_data["va_date"],  # C - Date
    f"{charlotte_data['app_match']} {charlotte_data['name']}",  # D - Name + match
    charlotte_data["market"],  # E - Market
    f"✅ {charlotte_data['rec']} ({charlotte_data['confidence']})",  # F - Rec
    f"=HYPERLINK(\"{charlotte_data['va_link']}\", \"▶️ Watch\")",  # G - VideoAsk link
    charlotte_data["name"].split()[0],  # H - First name
    charlotte_data["doc_id"],  # I - App ID
    charlotte_data["email"],  # J - Email
    charlotte_data["phone_formatted"],  # K - Phone
    f"=HYPERLINK(\"{charlotte_data['zd_link']}\", \"🔍\")",  # L - Zendesk link
    f"=TEXT(TODAY(),\"MM/DD\") & \" Intro Call Passed. \" & \"{charlotte_data['loc_drive']}\" & \"; {charlotte_data['exp_str']}\"",  # M - Zendesk approved note
    f"=TEXT(TODAY(),\"MM/DD\") & \" Not Hiring — Intro Call. \" & \"{charlotte_data['city']}\"",  # N - Zendesk denied note
    charlotte_data["exp_str"],  # O - Experience
    charlotte_data["loc_drive"],  # P - Location/Drive
    charlotte_data["sched_str"],  # Q - Schedule
    charlotte_data["summary"],  # R - AI Summary
    "; ".join(charlotte_data["red_flags"]),  # S - Red Flags
    charlotte_data["transcripts"]["q3"],  # T - Q3 transcript
    charlotte_data["transcripts"]["q4"],  # U - Q4 transcript
    charlotte_data["transcripts"]["q5"],  # V - Q5 transcript
    charlotte_data["transcripts"]["q6"],  # W - Q6 transcript
    charlotte_data["transcripts"]["q7"]   # X - Q7 transcript
]

print("Row data to append:")
print(row_data)

# Build the gws command
cmd = [
    'gws', 'sheets', 'spreadsheets', 'values', 'append',
    '--params', json.dumps({
        'spreadsheetId': '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0',
        'range': 'Backlog Reviews!A2:X',
        'valueInputOption': 'USER_ENTERED'
    }),
    '--json', json.dumps({
        'values': [row_data]
    })
]

print("Command:", " ".join(cmd))

result = subprocess.run(cmd, env={**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'})
print("Return code:", result.returncode)