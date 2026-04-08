#!/usr/bin/env python3
import json, requests, sys, os
from datetime import datetime, timezone, timedelta

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'

QUESTION_IDS = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

def get_answers(token, qid, contact_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'organization-id': ORG_ID
    }
    url = f'https://api.videoask.com/questions/{qid}/answers?limit=50'
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return ''
    data = resp.json()
    for ans in data.get('results', []):
        if ans.get('contact_id') == contact_id:
            return ans.get('transcription', '')
    return ''

def main():
    # Load token
    with open(f'{CREDENTIALS_DIR}/videoask-token.json') as f:
        token_data = json.load(f)
    token = token_data['access_token']
    
    # Check token expiry
    obtained = token_data.get('obtained_at', '')
    expires_in = token_data.get('expires_in', 86400)
    if obtained:
        obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
        expires_at = obtained_dt + timedelta(seconds=expires_in)
        now = datetime.now(timezone.utc)
        if expires_at < now:
            print(json.dumps({'error': 'TOKEN_EXPIRED', 'new_count': 0}))
            return
    
    # Get contacts
    headers = {
        'Authorization': f'Bearer {token}',
        'organization-id': ORG_ID
    }
    resp = requests.get(f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=100', headers=headers, timeout=10)
    if resp.status_code != 200:
        print(json.dumps({'error': f'API_FAILED_{resp.status_code}', 'new_count': 0}))
        return
    
    data = resp.json()
    contacts = data.get('results', [])
    completed = [c for c in contacts if c.get('status') == 'completed']
    
    # Load processed contacts
    with open(f'{WORKSPACE}/videoask-state.json') as f:
        state = json.load(f)
    processed = set(state.get('processed_contacts', []))
    
    new_completed = [c for c in completed if c['contact_id'] not in processed]
    
    if not new_completed:
        print(json.dumps({'new_count': 0, 'candidates': [], 'error': None}))
        return
    
    # Take first candidate only (max 2 per run, but we'll do 1 for now)
    contact = new_completed[0]
    cid = contact['contact_id']
    name = contact.get('name', '')
    email = contact.get('email', '')
    phone = contact.get('phone_number', '')
    created = contact.get('created_at', '')
    
    # Get transcripts
    transcripts = {}
    for qkey, qid in QUESTION_IDS.items():
        transcripts[qkey] = get_answers(token, qid, cid) or ''
    
    # Count answered questions
    q_count = sum(1 for q in ['q3','q4','q5','q6','q7'] if transcripts.get(q, '').strip())
    
    # Market detection
    market = 'unknown'
    if phone:
        area_code = phone[2:5] if phone.startswith('+1') else ''
        if area_code in ['801','385','435']:
            market = 'UT'
        elif area_code in ['404','470','678','770','762','706','912','229','478']:
            market = 'GA'
        elif area_code in ['480','602','623','520','928']:
            market = 'AZ'
        else:
            market = 'UNKNOWN'
    
    # Experience detection
    q3_text = transcripts.get('q3', '').lower()
    exp_type = 'none'
    if any(word in q3_text for word in ['daycare', 'preschool', 'teacher', 'classroom', 'substitute', 'para', 'head start', 'camp counselor']):
        exp_type = 'formal'
    elif any(word in q3_text for word in ['babysit', 'nanny', 'own children', 'relative', 'sibling']):
        exp_type = 'informal'
    elif 'experience' in q3_text or 'worked' in q3_text or 'coaching' in q3_text:
        exp_type = 'mixed'
    
    # Simple evaluation
    if exp_type == 'formal':
        rec = '✅'
        conf = 'HIGH'
    elif exp_type == 'informal' and market != 'AZ':
        rec = '✅'
        conf = 'MEDIUM'
    elif exp_type == 'mixed' and market != 'AZ':
        rec = '✅'
        conf = 'MEDIUM'
    else:
        rec = '🟡'
        conf = 'MEDIUM'
    
    candidate = {
        'contact_id': cid,
        'name': name,
        'email': email,
        'phone': phone,
        'market': market,
        'va_date': created[:10],
        'rec': rec,
        'confidence': conf,
        'exp_type': exp_type,
        'questions_answered': q_count,
        'transcripts': transcripts,
    }
    
    output = {
        'new_count': 1,
        'candidates': [candidate],
        'error': None
    }
    
    print(json.dumps(output))

if __name__ == '__main__':
    main()