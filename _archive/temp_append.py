import json
import subprocess
import sys

# Destiny Scott row
destiny_row = [
    "FALSE",  # A: Reviewed
    "FALSE",  # B: Erica Approved
    "2026-04-06",  # C: va_date
    "🟢 Destiny  Scottt",  # D: app_match emoji + name
    "georgia",  # E: market
    "✅ LOW",  # F: rec emoji + confidence
    '=HYPERLINK("https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/fdaefd96-0348-4ea4-a716-b402c42b92b8","▶️ Watch")',  # G: VideoAsk link
    "Destiny",  # H: first_name
    "LUY0WWc46tYVqo8VFIcCM9PyTMj2",  # I: doc_id
    "destinytofye234@gmail.com",  # J: email
    "(912) 432-8353",  # K: phone_formatted
    '=HYPERLINK("https://upkid.zendesk.com/agent/search/1?q=destinytofye234@gmail.com","🔍")',  # L: Zendesk link
    '=TEXT(TODAY(),"MM/DD") & " Intro Call Passed. " & "East Point Georgia., 5-10mi. 2 years working with kids but details vague, CPR expired but can renew, available full-time and part-time."',  # M: Zendesk approved note
    '=TEXT(TODAY(),"MM/DD") & " Not Hiring — Intro Call. " & "East Point Georgia. Vague experience details, insufficient information for approval."',  # N: Zendesk denied note
    "Mentions kids exp, vague",  # O: exp_str
    "East Point Georgia.\n and, 5-10mi",  # P: loc_drive
    "FT, PT",  # Q: sched_str
    "Destiny has 2 years of experience working with kids but her transcript is vague and incomplete. She mentions her CPR certificate expired but she can get it again. Her conflict resolution answer is practical (taking turns with toys), but she only answered 4/5 questions and didn't answer \"Why Great.\" Georgia prefers formal experience, and her vague \"working with kids\" doesn't specify setting. This is a judgment call for Erica — could be approved as entry-level, but confidence is LOW due to lack of specifics.",  # R: AI summary
    "",  # S: red_flags
    "Hello, my name is Destiny, Scott. I've been working with kids for the past two years. I believe I have a passion for children. I love working with kids.\n I think.\n My CPR and stuff. My CPR training stuff expired, but I can get it again, but I have all of my other certificates and stuff like that.",  # T: q3
    "I live in East Point Georgia.\n and,\n I can travel like 5 to 10 miles.",  # U: q4
    "I'm looking for part-time and full-time.",  # V: q5
    "How I would deal with conflict when two children fight is usually because sharing or miscommunication or something of that nature. So I would just either if they couldn't share the toys, I would take it from both of them, or I would let them take, turns five minutes on each for each one, for, with the toy. And then after that, the first five minutes,\n then the next one will get a turn.",  # W: q6
    "",  # X: q7 (empty since not answered)
]

# Convert to JSON array
json_values = json.dumps([destiny_row])
print(json_values)

# Run the command
cmd = [
    "gws", "sheets", "+append",
    "--spreadsheet", "1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0",
    "--json-values", json_values
]

env = {"GOOGLE_WORKSPACE_CLI_CONFIG_DIR": "/Users/tylerbot/.config/gws-write"}
result = subprocess.run(cmd, env=env, capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)