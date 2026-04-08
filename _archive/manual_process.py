#!/usr/bin/env python3
"""
Manual processing of VideoAsk submissions - simplified to avoid security blocks.
"""
import json
import subprocess
import re
import os
import sys
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

AREA_CODE_MARKET = {
    '801': 'utah', '385': 'utah', '435': 'utah',
    '404': 'georgia', '470': 'georgia', '678': 'georgia', '770': 'georgia',
    '762': 'georgia', '706': 'georgia', '912': 'georgia', '229': 'georgia', '478': 'georgia',
    '480': 'arizona', '602': 'arizona', '623': 'arizona', '520': 'arizona', '928': 'arizona',
}

def load_state():
    with open(f'{WORKSPACE}/videoask-state.json') as f:
        return json.load(f)

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
        if status_code == 401 or status_code == 403:
            return None, 'TOKEN_EXPIRED'
        if status_code >= 400:
            return None, f'HTTP_{status_code}'
        cleaned = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b' ', body)
        return json.loads(cleaned), None
    return None, 'UNKNOWN'

def get_transcripts(contact_id, token):
    """Get transcripts for Q3-Q7 for a contact."""
    transcripts = {}
    for q_name, q_id in QUESTION_IDS.items():
        url = f'https://api.videoask.com/questions/{q_id}/answers?limit=20'
        data, error = va_api(url, token)
        if error or not data:
            transcripts[q_name] = ''
            continue
        for answer in data.get('results', []):
            if answer.get('contact_id') == contact_id:
                transcripts[q_name] = answer.get('transcription', '')
                break
        if q_name not in transcripts:
            transcripts[q_name] = ''
    return transcripts

def get_area_code(phone):
    digits = re.sub(r'[^\d]', '', phone)
    if digits.startswith('1') and len(digits) == 11: return digits[1:4]
    elif len(digits) == 10: return digits[:3]
    return ''

def detect_experience_type(q3):
    if not q3: return 'unknown'
    q3_lower = q3.lower()
    FORMAL = ['daycare','preschool','head start','montessori','after school','camp counselor',
              'summer camp','ymca','boys and girls club','classroom','teacher','substitute',
              'kindergarten','elementary','learning center','child development','tutor','school']
    INFORMAL = ['babysit','nanny','own children','my kids','niece','nephew','sibling']
    has_formal = any(kw in q3_lower for kw in FORMAL)
    has_informal = any(kw in q3_lower for kw in INFORMAL)
    if has_formal and has_informal: return 'mixed'
    if has_formal: return 'formal'
    if has_informal: return 'informal'
    if any(w in q3_lower for w in ['experience','worked with','children','kids']): return 'unclear'
    return 'none'

def evaluate(candidate):
    """Evaluate a candidate."""
    exp_type = candidate['exp_type']
    market = candidate['market']
    q_count = candidate['questions_answered']
    
    if exp_type == 'formal' and q_count >= 4:
        if market == 'arizona':
            return 'APPROVE', 'MEDIUM'
        return 'APPROVE', 'HIGH'
    elif exp_type == 'mixed':
        return 'APPROVE', 'MEDIUM'
    elif exp_type == 'informal':
        if market == 'utah': return 'APPROVE', 'MEDIUM'
        if market == 'arizona': return 'FLAG', 'HIGH'
        return 'FLAG', 'MEDIUM'
    elif exp_type == 'none':
        return 'FLAG', 'LOW'
    elif exp_type == 'unclear':
        return 'APPROVE', 'LOW'
    else:
        return 'FLAG', 'LOW'

def main():
    # Load token
    with open(f'{CREDENTIALS_DIR}/videoask-token.json') as f:
        token_data = json.load(f)
    token = token_data['access_token']
    
    # Load state
    state = load_state()
    processed = set(state['processed_contacts'])
    
    # Fetch completed contacts
    url = f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=20&status=completed'
    data, error = va_api(url, token)
    if error:
        if error == 'TOKEN_EXPIRED':
            print(json.dumps({'status': 'error', 'error': 'TOKEN_EXPIRED'}))
            return
        print(json.dumps({'status': 'error', 'error': error}))
        return
    
    # Filter new contacts
    new_contacts = []
    for contact in data.get('results', []):
        cid = contact.get('contact_id')
        if cid and cid not in processed:
            new_contacts.append(contact)
    
    # Process max 2
    candidates = []
    for contact in new_contacts[:MAX_PER_RUN]:
        cid = contact['contact_id']
        name = contact.get('name', '').title()
        email = contact.get('email', '')
        phone = contact.get('phone_number', '')
        created = contact.get('created_at', '')
        platform = contact.get('platform', '')
        
        # Get transcripts
        transcripts = get_transcripts(cid, token)
        
        # Count answered questions
        questions_answered = sum(1 for t in transcripts.values() if t and t.strip())
        
        # Determine market
        area_code = get_area_code(phone)
        market = AREA_CODE_MARKET.get(area_code, 'unknown')
        
        # Experience type
        exp_type = detect_experience_type(transcripts.get('q3', ''))
        
        # Evaluate
        rec, confidence = evaluate({
            'exp_type': exp_type,
            'market': market,
            'questions_answered': questions_answered
        })
        
        candidate = {
            'contact_id': cid,
            'name': name,
            'email': email,
            'phone': phone,
            'phone_formatted': re.sub(r'[^\d]', '', phone),
            'created_at': created,
            'platform': platform,
            'market': market,
            'exp_type': exp_type,
            'recommendation': rec,
            'confidence': confidence,
            'questions_answered': questions_answered,
            'transcripts': transcripts,
            'va_link': f'https://app.videoask.com/app/organizations/{ORG_ID}/form/{FORM_ID}/conversation/{cid}',
            'zd_link': f'https://upkid.zendesk.com/agent/search/1?q={email}',
        }
        candidates.append(candidate)
    
    output = {
        'new_count': len(candidates),
        'total_checked': len(data.get('results', [])),
        'candidates': candidates,
        'pending_match_count': len(state.get('pending_match', [])),
    }
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()