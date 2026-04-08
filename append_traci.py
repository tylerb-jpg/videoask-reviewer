#!/usr/bin/env python3
import json
import subprocess
import os

# Traci's data
traci_data = {
    "contact_id": "8a70600a-f2c5-4267-89fd-3e19035db713",
    "name": "Traci Nickerson",
    "email": "dsdcts@gmail.com",
    "phone": "+18012315189",
    "phone_formatted": "(801) 231-5189",
    "market": "utah",
    "va_date": "2026-04-07",
    "rec": "APPROVE",
    "confidence": "HIGH",
    "exp_type": "formal",
    "exp_str": "25yr",
    "city": "Layton, UT",
    "drive": "",
    "loc_drive": "Layton, UT",
    "sched_str": "FT",
    "questions_answered": 5,
    "app_match": "🟢",
    "app_name": "Traci Nickerson",
    "doc_id": "5YfECEPXXEMZCpxoqYK1RCWMJYM2",
    "red_flags": [],
    "va_link": "https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/8a70600a-f2c5-4267-89fd-3e19035db713",
    "zd_link": "https://upkid.zendesk.com/agent/search/1?q=dsdcts@gmail.com",
    "summary": "Traci brings 25 years of formal experience in the Davis School District and comes across as very reliable and experienced. Her approach to conflict resolution shows professionalism and she's clearly motivated to keep her home with steady full-time work. This is a strong candidate for Utah's more lenient market.",
    "transcripts": {
        "q3": "Hi, I'm Tracy and I work for the Davis School, District for 25 years. I've raised two boys and I do love working with kids.\n And I just I just see that as something that is a positive thing in life. You can go home at night and know that you've impacted a child's life. So anyway, that's a little bit about me. I have my home in Layton and I'm working really hard.\n To get a job and keep that home. So yeah, I would be very, very interested.\n I am more looking at full-time work versus part-time.\n But I know it says you can make your own schedule.",
        "q4": "I am located in Layton Utah and\n I am not objected to traveling a little bit.\n But that is where I am majorly located, so it would be nice to have something there.",
        "q5": "I am looking for full-time work. It just depends on what you guys offer in my area. And I would\n Be flexible to pretty much any hours that you need.",
        "q6": "That's an interesting question.\n One child hits another. Then I think the best thing to do is separate the children, talk to them individually and get them to reason with each other if you can, but depending on the grade,\n You might have to involve the parent at some point. However, I think that if you can get them to just talk to each other kind of sit in the Middle with them and reason with both of them, then I think it could be a productive.\n Aang.",
        "q7": "I have a lot of motivation and I have a lot of passion and I believe that I would be a great teacher because I could\n be encouraging raising two kids of my own.\n Knowing that it's very difficult to control every single entire child. But I do think that\n I have an ability to talk and communicate and be soft with kids and and they'll understand and\n Yeah, that's all. That's all I can really say."
    }
}

# Build the row data
row_data = [
    "FALSE",  # A - Reviewed checkbox
    "FALSE",  # B - Erica Approved checkbox
    traci_data["va_date"],  # C - Date
    f"{traci_data['app_match']} {traci_data['name']}",  # D - Name + match
    traci_data["market"],  # E - Market
    f"✅ {traci_data['rec']} ({traci_data['confidence']})",  # F - Rec
    f"=HYPERLINK(\"{traci_data['va_link']}\", \"▶️ Watch\")",  # G - VideoAsk link
    traci_data["name"].split()[0],  # H - First name
    traci_data["doc_id"],  # I - App ID
    traci_data["email"],  # J - Email
    traci_data["phone_formatted"],  # K - Phone
    f"=HYPERLINK(\"{traci_data['zd_link']}\", \"🔍\")",  # L - Zendesk link
    f"=TEXT(TODAY(),\"MM/DD\") & \" Intro Call Passed. \" & \"{traci_data['loc_drive']}\" & \"; {traci_data['exp_str']}\"",  # M - Zendesk approved note
    f"=TEXT(TODAY(),\"MM/DD\") & \" Not Hiring — Intro Call. \" & \"{traci_data['city']}\"",  # N - Zendesk denied note
    traci_data["exp_str"],  # O - Experience
    traci_data["loc_drive"],  # P - Location/Drive
    traci_data["sched_str"],  # Q - Schedule
    traci_data["summary"],  # R - AI Summary
    "; ".join(traci_data["red_flags"]),  # S - Red Flags
    traci_data["transcripts"]["q3"],  # T - Q3 transcript
    traci_data["transcripts"]["q4"],  # U - Q4 transcript
    traci_data["transcripts"]["q5"],  # V - Q5 transcript
    traci_data["transcripts"]["q6"],  # W - Q6 transcript
    traci_data["transcripts"]["q7"]   # X - Q7 transcript
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