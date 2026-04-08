#!/usr/bin/env python3
import subprocess
import json
import sys

# Read credentials path from env or use default
import os
creds_dir = os.path.expanduser("~/.config/gws-write")
token_path = os.path.join(creds_dir, "application_default_credentials.json")

# Use gws to append row via batchUpdate directly? Actually let's use sheets.spreadsheets.values.append
# But we need to construct proper API call via gws

# Simpler: use gws command with properly escaped JSON via file
# Actually gws +append takes --json-values as string, let's just call it with proper quoting

row = [
  "FALSE","FALSE","2026-04-08","✅ Shuntae Hunter","georgia","🟡 APPROVE (MEDIUM)",
  "=HYPERLINK(\"https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/af372992-a086-4593-81ec-8e2819fcc3dc\",\"VA Link\")",
  "shuntae","3aHtxEr9CtTOsUoC8R5GIaxjCP82","msshuntaehunter@gmail.com","(470) 694-3372",
  "=HYPERLINK(\"https://upkid.zendesk.com/agent/search/1?q=msshuntaehunter@gmail.com\",\"ZD Link\")",
  "2026-04-08 Intro Call Passed. Shuntae lives in Atlanta, GA with a 25-30 mile drive radius. She has 13 years of mixed childcare experience (daycare and nanny) and is seeking part-time work. She shows strong patience and conflict resolution skills.",
  "2026-04-08 Not Hiring — Intro Call. Location and experience unclear for Georgia market.",
  "mixed: 13yr total (daycare + nanny)","Atlanta, GA, 25-30mi","PT",
  "Mixed experience: 13 years across daycare and nanny roles. Shows strong patience, conflict resolution skills, and enthusiasm for returning to childcare after corporate break. Good communication.",
  "None",
  "Hi, my name is shuntae hunter and I currently live in Atlanta. Georgia...",
  "I am I want to work part-time. And I have a lot of flexibilities...",
  "So how I feel with chilled conflict between two children...",
  "I will be a great kid teacher. I am very compassionate..."
]

json_str = json.dumps([row], ensure_ascii=False)
# Escape for shell
import shlex
# We'll pass via stdout to gws? No, gws wants it as arg.
# Use environment variable approach instead? gws doesn't support it.
# Let's just use subprocess with shell=False and pass the arg correctly

result = subprocess.run(
  ["gws", "sheets", "+append", "--spreadsheet", "1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0", "--json-values", json_str],
  env={**os.environ, "GOOGLE_WORKSPACE_CLI_CONFIG_DIR": os.path.expanduser("~/.config/gws-write")},
  capture_output=True, text=True
)
print(result.stdout)
print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
