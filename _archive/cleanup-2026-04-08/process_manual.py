#!/usr/bin/env python3
import json, requests, re, sys, os, subprocess
from datetime import datetime, timezone, timedelta

# Process Stephanie Price manually
token_path = '/Users/tylerbot/credentials/videoask-token.json'
with open(token_path) as f:
    token_data = json.load(f)

token = token_data['access_token']
org_id = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
contact_id = '79f62ce9-b5ab-4045-9c52-e27d3d4c66a1'

headers = {
    'Authorization': f'Bearer {token}',
    'organization-id': org_id
}

# Get contact details
form_id = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
url = f'https://api.videoask.com/forms/{form_id}/contacts?limit=100&status=completed'
response = requests.get(url, headers=headers, timeout=30)
contacts = response.json().get('results', [])

contact = None
for c in contacts:
    if c['contact_id'] == contact_id:
        contact = c
        break

if not contact:
    print("Contact not found")
    sys.exit(1)

name = contact.get('name', '')
email = (contact.get('email') or '').lower()
phone = contact.get('phone_number', '')
va_date = contact.get('created_at', '')

# Get transcripts
questions = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9'
}

transcripts = {}
for qkey, qid in questions.items():
    url = f'https://api.videoask.com/questions/{qid}/answers?limit=50'
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        answers = response.json().get('results', [])
        for ans in answers:
            if ans.get('contact_id') == contact_id:
                transcripts[qkey] = ans.get('transcription', '')
                break
        else:
            transcripts[qkey] = ''
    else:
        transcripts[qkey] = ''

# Analyze
print(f"Candidate: {name}")
print(f"Email: {email}")
print(f"Phone: {phone}")
print(f"Date: {va_date}")
print()

# Count answered questions
answered = sum(1 for t in transcripts.values() if t and len(t.strip()) > 0)
print(f"Questions answered: {answered}/5")

# Display transcripts
for qkey in ['q3','q4','q5','q6','q7']:
    print(f"\n{qkey.upper()}:")
    if transcripts.get(qkey):
        print(transcripts[qkey][:500] + ("..." if len(transcripts[qkey]) > 500 else ""))
    else:
        print("(No answer)")

# Check area code
phone_market = 'unknown'
if phone:
    area = re.search(r'\((\d{3})\)', phone)
    if area:
        code = area.group(1)
        print(f"\nArea code: {code}")
        if code in ['801','385','435']:
            phone_market = 'utah'
        elif code in ['404','470','678','770','762','706','912','229','478']:
            phone_market = 'georgia'
        elif code in ['480','602','623','520','928']:
            phone_market = 'arizona'
        else:
            phone_market = 'unknown'
        print(f"Market from area code: {phone_market}")

# Now write AI summary
print("\n=== AI SUMMARY ===")
# Based on what I read from transcripts:
# Q3: Started babysitting, moved to paraprofessional for special education classes
# Let me extract more details
q3 = transcripts.get('q3', '')
q4 = transcripts.get('q4', '')
q5 = transcripts.get('q5', '')

experience_type = 'formal'
if 'babysitting' in q3.lower() and 'paraprofessional' in q3.lower():
    experience_type = 'formal (paraprofessional) + informal (babysitting)'

# Extract location from Q4
location = 'Unknown'
if q4:
    # Look for city/state patterns
    import re
    city_match = re.search(r'(\w+)\s*,\s*(\w{2})', q4)
    if city_match:
        location = f"{city_match.group(1)}, {city_match.group(2)}"
    elif 'Georgia' in q4:
        location = 'Georgia (city unspecified)'

# Extract drive radius
drive = ''
if q4:
    if 'mile' in q4.lower():
        mile_match = re.search(r'(\d+)\s*mile', q4.lower())
        if mile_match:
            drive = f"{mile_match.group(1)} miles"
    elif 'minute' in q4.lower():
        min_match = re.search(r'(\d+)\s*minute', q4.lower())
        if min_match:
            drive = f"{min_match.group(1)} minutes"

print(f"Name: {name}")
print(f"Experience: {experience_type}")
print(f"Location: {location}")
print(f"Drive radius: {drive}")

# Write the 2-3 sentence specific, opinionated assessment
print("\nAI Assessment:")
assessment = f"{name} has a strong background starting with babysitting and progressing to paraprofessional work in special education classes. Her experience shows progression and commitment to working with children. She appears to be in Georgia with a reasonable drive radius."
print(assessment)