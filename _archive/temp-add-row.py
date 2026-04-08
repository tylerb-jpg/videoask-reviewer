#!/usr/bin/env python3
import subprocess, json, os, sys

# Environment
GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'

# Ava Register candidate data
row_values = [
    False,
    False,
    "2026.04.06",
    "🟢 Ava Register",
    "Georgia",
    "🟡 MEDIUM",
    '=HYPERLINK("https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/7e6bbf2e-db5d-40d9-a51e-e033b0ed7a7d", "▶️ Watch")',
    "Ava",
    "YI3qZUdDNgPCeYXdQXLV7L0PtJq1",
    "avaregister905@gmail.com",
    "(770) 601-4889",
    '=HYPERLINK("https://upkid.zendesk.com/agent/search/1?q=avaregister905@gmail.com", "🔍")',
    '=TEXT(TODAY(),"MM/DD") & " Intro Call Passed. Bethlehem Georgia, 30mi. 12 years babysitting experience across all ages, early childhood education major at Georgia Gwinnett College. Available full-time or part-time around school schedule (Tues/Thurs morning class only)."',
    '=TEXT(TODAY(),"MM/DD") & " Not Hiring — Intro Call. Bethlehem Georgia. Only informal babysitting experience; Georgia typically requires formal daycare experience."',
    "12yr; babysitter; education student",
    "Bethlehem Georgia, 30mi",
    "FT, PT, around school",
    "Ava has 12 years of babysitting experience across all age groups and is an early childhood education major at Georgia Gwinnett College. Her conflict resolution answer shows maturity and practical skills — she separated children, ensured safety, and facilitated genuine apologies. Georgia typically prefers formal daycare experience, but her extensive babysitting history combined with her education path makes this a judgment call for Erica.",
    "",
    "Hi, my name is Ava register. I have a lot of previous experience in Babysitting and watching children. I've done ages between nine to ten months all the way up to 12 years old. I kept a families kids for about eight consecutive years until they moved to where I could not travel to keep them anymore. I am a early childhood education. Major at Georgetown.\n Georgia Gwinnett College, and I have an extreme passion for working with kids and childcare.",
    "I live in Bethlehem Georgia and I'm willing to travel between 20 and 30 minutes away.",
    "I am looking for both full-time or part-time work. I am currently a college student, but I take one class on Tuesdays and Thursdays for an hour in the mornings 8 a.m. to 9 a.m. So I am available to work after that on those two days. Other than that I am open to six days a week. No Sundays.",
    "Previously babysitting, I have dealt with kids from two separate families and also with kids that were siblings and related to each other. With that being said, I have had an older child. He was about 11 years old and he hit another eight year old little boy. I handled the situation with ease and I separated the two children. I apologized to the one that got hit.\n And I made sure that he was okay, first and foremost and then I did discipline the other and I told him, you know, that he needed to apologize and be genuine with his apology. And I did make him take a break to calm down, and reconsider his actions, and then we went back to play time. He apologized and we moved on.",
    "I would make a great up kid teacher, because I have an extreme passion for childcare and the education system. A lot of my family members have worked in education system in Barrow, County, and it has really inspired me to want to help the Next Generation who is coming up."
]

# Build command
cmd = [
    'gws', 'sheets', 'spreadsheets', 'values', 'append',
    '--params', json.dumps({
        'spreadsheetId': SPREADSHEET_ID,
        'range': 'Backlog Reviews!A:X',
        'valueInputOption': 'USER_ENTERED'
    }),
    '--json', json.dumps({'values': [row_values]})
]

# Run
print(f"Running command: {' '.join(cmd[:6])} ...")
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    env=GWS_ENV
)

print("Exit code:", result.returncode)
print("Stdout:", result.stdout)
print("Stderr:", result.stderr)

if result.returncode != 0:
    sys.exit(1)