#!/usr/bin/env python3
import json, requests, sys, os, re
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

AREA_CODE_MARKET = {
    '801': 'utah', '385': 'utah', '435': 'utah',
    '404': 'georgia', '470': 'georgia', '678': 'georgia', '770': 'georgia',
    '762': 'georgia', '706': 'georgia', '912': 'georgia', '229': 'georgia', '478': 'georgia',
    '480': 'arizona', '602': 'arizona', '623': 'arizona', '520': 'arizona', '928': 'arizona',
}

def get_answers(token, qid, contact_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'organization-id': ORG_ID
    }
    url = f'https://api.videoask.com/questions/{qid}/answers?limit=50'
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return None
    data = resp.json()
    for ans in data.get('results', []):
        if ans.get('contact_id') == contact_id:
            return ans.get('transcription', '')
    return ''

def extract_city(q4_text, market):
    if not q4_text:
        return ''
    q4_lower = q4_text.lower()
    if 'sandy springs' in q4_lower:
        return 'Sandy Springs, GA'
    elif 'atlanta' in q4_lower:
        return 'Atlanta, GA'
    elif 'augusta' in q4_lower:
        return 'Augusta, GA'
    elif 'savannah' in q4_lower:
        return 'Savannah, GA'
    elif 'macon' in q4_lower:
        return 'Macon, GA'
    elif 'provo' in q4_lower:
        return 'Provo, UT'
    elif 'salt lake' in q4_lower or 'salt lake city' in q4_lower:
        return 'Salt Lake City, UT'
    elif 'phoenix' in q4_lower:
        return 'Phoenix, AZ'
    elif 'tucson' in q4_lower:
        return 'Tucson, AZ'
    
    # Try to find city pattern
    import re
    city_match = re.search(r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', q4_text)
    if city_match:
        city = city_match.group(1)
        if market == 'georgia':
            return f'{city}, GA'
        elif market == 'utah':
            return f'{city}, UT'
        elif market == 'arizona':
            return f'{city}, AZ'
        else:
            return f'{city}'
    return ''

def extract_drive(q4_text):
    if not q4_text:
        return ''
    q4_lower = q4_text.lower()
    if 'willing to travel' in q4_lower or 'travel' in q4_lower:
        return 'willing to travel'
    if 'radius' in q4_lower:
        import re
        radius_match = re.search(r'(\d+)\s*mile', q4_lower)
        if radius_match:
            return f'{radius_match.group(1)} mile radius'
    return ''

def extract_exp(q3_text, exp_type):
    if not q3_text:
        return ''
    if exp_type == 'formal':
        return 'Formal childcare experience'
    elif exp_type == 'informal':
        return 'Informal experience (babysitting/nannying)'
    elif exp_type == 'mixed':
        return 'Mixed experience'
    else:
        return 'No stated experience'

def extract_sched(q5_text):
    if not q5_text:
        return ''
    q5_lower = q5_text.lower()
    if 'full-time' in q5_lower:
        return 'Full-time, open availability'
    elif 'part-time' in q5_lower:
        return 'Part-time'
    else:
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
    
    # Get first new contact
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
    
    # Take first candidate
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
    phone_market = 'unknown'
    if phone:
        area_code = phone[2:5] if phone.startswith('+1') else ''
        phone_market = AREA_CODE_MARKET.get(area_code, 'unknown')
        market = phone_market
    
    # Experience detection
    q3_text = transcripts.get('q3', '').lower()
    exp_type = 'none'
    if any(word in q3_text for word in ['daycare', 'preschool', 'teacher', 'classroom', 'substitute', 'para', 'head start', 'camp counselor']):
        exp_type = 'formal'
    elif any(word in q3_text for word in ['babysit', 'nanny', 'own children', 'relative', 'sibling']):
        exp_type = 'informal'
    elif 'experience' in q3_text or 'worked' in q3_text or 'coaching' in q3_text:
        exp_type = 'mixed'
    
    # Extract structured data
    city = extract_city(transcripts.get('q4'), market)
    drive = extract_drive(transcripts.get('q4'))
    exp_str = extract_exp(transcripts.get('q3'), exp_type)
    sched_str = extract_sched(transcripts.get('q5'))
    
    # Evaluation
    if exp_type == 'formal':
        rec = '✅'
        conf = 'HIGH'
    elif exp_type == 'informal' and market != 'arizona':
        rec = '✅'
        conf = 'MEDIUM'
    elif exp_type == 'mixed' and market != 'arizona':
        rec = '✅'
        conf = 'MEDIUM'
    else:
        rec = '🟡'
        conf = 'MEDIUM'
    
    # Red flags
    flags = []
    first_name = name.split()[0].lower() if name else ''
    MALE_NAMES = {'brian','john','matt','matthew','jarvis','james','george','nicholas','nico',
                  'josue','elan','denetric','brodie','robert','michael','david','daniel','joseph',
                  'william','richard','charles','thomas','chris','jason','ryan','kevin','brandon'}
    if first_name in MALE_NAMES:
        flags.append('👨 MALE — centers may not place')
    
    if phone_market != 'unknown' and phone_market != market:
        flags.append(f'📞 Area code = {phone_market.title()}')
    
    # VideoAsk dashboard link
    va_link = f'https://app.videoask.com/app/organizations/{ORG_ID}/form/{FORM_ID}/conversation/{cid}'
    
    # Zendesk search link
    email_enc = email.replace('+', '%2B')
    zd_link = f'https://upkid.zendesk.com/agent/search/1?q={email_enc}'
    
    # Format phone
    def fmt_phone(p):
        if not p:
            return ''
        if p.startswith('+1'):
            return f'({p[2:5]}) {p[5:8]}-{p[8:]}'
        return p
    
    candidate = {
        'contact_id': cid,
        'name': name,
        'email': email,
        'phone': phone,
        'phone_formatted': fmt_phone(phone),
        'market': market.upper() if market != 'unknown' else 'UNKNOWN',
        'va_date': created[:10],
        'rec': rec,
        'confidence': conf,
        'exp_type': exp_type,
        'exp_str': exp_str,
        'city': city,
        'drive': drive,
        'loc_drive': city + (f", {drive}" if drive else ""),
        'sched_str': sched_str,
        'questions_answered': q_count,
        'app_match': '🔴',  # Default - not found yet
        'app_name': 'Not found',
        'doc_id': '',
        'mismatches': '',
        'red_flags': flags,
        'va_link': va_link,
        'zd_link': zd_link,
        'is_duplicate': False,
        'transcripts': transcripts,
        'first_name': name.split()[0] if name else '',
    }
    
    output = {
        'new_count': 1,
        'candidates': [candidate],
        'error': None
    }
    
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()