#!/usr/bin/env python3
import json, requests, re

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

# Get all transcripts for this contact
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

print("Stephanie Price Transcripts:")
print("\nQ3 - Experience:")
print(transcripts.get('q3', '')[:500])
print("\nQ4 - Location:")
print(transcripts.get('q4', ''))
print("\nQ5 - Schedule:")
print(transcripts.get('q5', ''))
print("\nQ6 - Conflict:")
print(transcripts.get('q6', '')[:300])
print("\nQ7 - Why Great:")
print(transcripts.get('q7', '')[:300])

# Count answered questions
answered = sum(1 for t in transcripts.values() if t and len(t.strip()) > &found)0)
print(f"\nQuestions answered: {answered}/5")

# Check phone area code
phone = ''
form_id = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
url = f'https://api.videoask.com/forms/{form_id}/contacts?limit=100&status=completed'
response = requests.get(url, headers=headers, timeout=30)
if response.status_code == 200:
    contacts = response.json().get('results', [])
    for c in contacts:
        if c['contact_id'] == contact_id:
            phone = c.get('phone_number', '')
            print(f"\nPhone: {phone}")
            break

if phone:
    area = re.search(r'\((\d{3})\)', phone)
    if area:
        code = area.group(1)
        print(f"Area code: {code}")
        if code in ['801','385','435']:
            market = 'utah'
        elif code in ['404','470','678','770','762','706','912','229','478']:
            market = 'georgia'
        elif code in ['480','602','623','520','928']:
            market = 'arizona'
        else:
            market = 'unknown'
        print(f"Market from area code: {market}")