#!/usr/bin/env python3
import json, subprocess, sys, os, re
from datetime import datetime, timezone, timedelta

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
MAX_PER_RUN = 2

QUESTION_IDS = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

def get_token():
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    with open(token_path) as f:
        token_data = json.load(f)
    obtained = token_data.get('obtained_at', '')
    expires_in = token_data.get('expires_in', 86400)
    if obtained:
        obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
        expires_dt = obtained_dt + timedelta(seconds=expires_in - 300)
        if datetime.now(timezone.utc) > expires_dt:
            print("TOKEN_EXPIRED", file=sys.stderr)
            return None
    return token_data['access_token']

def curl_get(url):
    token = get_token()
    if not token:
        return None
    cmd = ['curl', '-s', '-w', '\n%{http_code}', url,
           '-H', f'Authorization: Bearer {token}',
           '-H', f'organization-id: {ORG_ID}']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    lines = result.stdout.strip().split('\n')
    if len(lines) < 2:
        return None
    body = '\n'.join(lines[:-1])
    status = lines[-1]
    if status != '200':
        return None
    try:
        return json.loads(body)
    except:
        return None

def main():
    # Load state
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    processed = set(state.get('processed_contacts', []))
    
    # Get contacts
    data = curl_get(f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=20')
    if not data:
        print(json.dumps({"error": "API_ERROR", "candidates": []}))
        return
    
    contacts = data.get('results', [])
    new_contacts = []
    for c in contacts:
        if c.get('status') == 'completed' and c.get('contact_id') not in processed:
            new_contacts.append(c)
            if len(new_contacts) >= MAX_PER_RUN:
                break
    
    if not new_contacts:
        print(json.dumps({"new_count": ICmpError, "candidates": []}))
        return
    
    candidates = []
    for c in new_contacts:
        cid = c['contact_id']
        
        # Get transcripts from answers
        transcripts = {}
        name, email, phone = '', '', ''
        market = 'unknown'
        
        for qname, qid in QUESTION_IDS.items():
            data = curl_get(f'https://api.videoask.com/questions/{qid}/answers?limit=50')
            if data:
                answers = data.get('results', [])
                matching = [a for a in answers if a.get('contact_id') == cid]
                if matching:
                    a = matching[0]
                    transcripts[qname] = a.get('transcription', '')
                    if not name:
                        name = a.get('contact_name', '')
                        email = a.get('contact_email', '')
                        phone = a.get('contact_phone_number', '')
        
        # Determine market from phone area code
        if phone:
            digits = re.sub(r'[^\d]', '', phone)
            if digits.startswith('1') and len(digits) == 11:
                digits = digits[1:]
            if len(digits) >= 3:
                area = digits[:3]
                if area in ['801', '385', '435']:
                    market = 'utah'
                elif area in ['404', '470', '678', '770', '762', '706', '912', '229', '478']:
                    market = 'georgia'
                elif area in ['480', '602', '623', '520', '928']:
                    market = 'arizona'
        
        # Basic evaluation from Q3 transcript
        rec = 'FLAG'
        confidence = 'LOW'
        q3_text = transcripts.get('q3', '').lower()
        if 'daycare' in q3_text or 'preschool' in q3_text or 'teacher' in q3_text:
            rec = 'APPROVE'
            confidence = 'MEDIUM'
        
        candidates.append({
            'contact_id': cid,
            'name': name,
            'email': email,
            'phone': phone,
            'market': market,
            'rec': rec,
            'confidence': confidence,
            'transcripts': transcripts,
            'questions_answered': sum(1 for t in transcripts.values() if t.strip()),
            'first_name': name.split()[0] if name else '',
        })
    
    print(json.dumps({
        'new_count': len(new_contacts),
        'candidates': candidates
    }, indent=2))

if __name__ == '__main__':
    main()