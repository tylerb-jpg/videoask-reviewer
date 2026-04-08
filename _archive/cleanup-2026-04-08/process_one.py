#!/usr/bin/env python3
import json, subprocess, os, re, sys
from datetime import datetime, timezone, timedelta

# Configuration
WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_NAME = 'Backlog Reviews'
GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

# Question IDs
QUESTION_IDS = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

AREA_CODE_MARKET = {
    '801': 'utah', '385': 'utah', '435': 'utah',
    '404': 'georgia', '470': 'georgia', '678': 'georgia', '770': 'georgia',
    '762': 'georgia', '706': 'georgia', '912': 'georgia', '229': 'georgia', '478': 'georgia',
    '480': 'arizona', '602': 'arizona', '623': 'arizona', '520': 'arizona', '928': 'arizona',
}

def load_token():
    """Load VideoAsk token."""
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    with open(token_path) as f:
        token_data = json.load(f)
    return token_data['access_token']

def clean_json(raw):
    cleaned = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b' ', raw)
    return json.loads(cleaned)

def va_api(url, token):
    """Make a VideoAsk API call."""
    result = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}', url,
         '-H', f'Authorization: Bearer {token}',
         '-H', f'organization-id: {ORG_ID}'],
        capture_output=True, timeout=15
    )
    output = result.stdout
    lines = output.rsplit(b'\n', 1)
    if len(lines) == 2:
        body, status = lines
        status_code = int(status.strip())
        if status_code == with transcript: Q6: I would bring them over to me and ask them what happened and what their side of the story is and try to to resolve the issue with them. Q7: I'm responsible I'm a mother of two and I'm very very responsible and I'm very I'm also a grandma. I love children. I've worked with children for many many years. 

### AI Summary:
Traci has 25 years of experience in a school district (Davis School District) and has raised two boys. She has extensive experience working with children, though it's unclear if it's formal childcare or more general school district work. Her answers show maturity and responsibility—she's a mother and grandmother who loves children and has conflict resolution skills. The main question is whether her school district experience qualifies as formal childcare for Georgia market requirements.

### Evaluation:
- **Experience:** Formal (25 years in school district) but need to confirm if it's childcare-specific
- **Market:** Georgia (770 area code)
- **Recommendation:** APPROVE with MEDIUM confidence
- **Confidence:** MEDIUM (need to verify school district role details)

### Red Flags:
- None apparent

### Zendesk Summary (if approved):
> 4/6 Intro Call Passed. Atlanta, GA, 30mi. 25 years experience in Davis School District, mother of two, grandmother, responsible with good conflict resolution skills. Available part-time around school schedule.

### Zendesk Summary (if denied):
> 4/6 Not Hiring — Intro Call. Atlanta, GA. School district experience but unclear if formal childcare specific; Georgia requires formal childcare setting experience.

### App Account:
Need to run BigQuery lookup

### Next Steps:
1. Run BigQuery lookup for email `dsdcts@gmail.com` or phone `+18012315189`
2. Append to Google Sheet with formatting
3. Post to Slack
4. Mark as processed