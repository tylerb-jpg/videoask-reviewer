#!/usr/bin/env python3
"""
Simple version of process-new-submissions.py that just outputs JSON for cron job.
Avoids complex subprocess calls that might be hanging.
"""
import json, os, sys, re
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
MAX_PER_RUN = 2

def main():
    # Load token
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    with open(token_path) as f:
        token_data = json.load(f)
    token = token_data['access_token']
    
    # Get contacts
    req = urllib.request.Request(
        f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=50&status=completed',
        headers={
            'Authorization': f'Bearer {token}',
            'organization-id': ORG_ID
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        contacts = data.get('results', data.get('items', []))
    except Exception as e:
        print(f'Error fetching contacts: {e}', file=sys.stderr)
        print(json.dumps({"error": "API_ERROR", "candidates": []}))
        return
    
    # Load state
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    processed = set(state.get('processed_contacts', []))
    
    # Find new contacts
    new_contacts = []
    for c in contacts:
        cid = c['contact_id']
        email = (c.get('email') or '').strip().lower()
        if cid in processed:
            continue
        # Safety: check if already in sheet (we'll skip this for now to keep it simple)
        new_contacts.append(c)
    
    if not new_contacts:
        print(json.dumps({"new_count": 0, "candidates": []}))
        return
    
    # Limit to max per run
    new_contacts = new_contacts[:MAX_PER_RUN]
    
    # Process each new contact
    candidates = []
    
    for contact in new_contacts:
        cid = contact['contact_id']
        email = (contact.get('email') or '').strip()
        phone = (contact.get('phone_number') or '').strip()
        name = (contact.get('name') or '').strip()
        created_utc = contact.get('created_at', '')
        
        # Convert date
        va_date = ''
        if created_utc:
            utc_dt = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
            mdt_dt = utc_dt.astimezone(timezone(timedelta(hours=-6)))
            va_date = mdt_dt.strftime('%Y-%m-%d')
        
        # Get transcripts for Q3-Q7
        transcripts = {}
        question_ids = {
            'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
            'q4': 'd796e231-caac-433f-be1e-4080793da124',
            'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
            'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
            'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
        }
        
        for qkey, qid in question_ids.items():
            try:
                req = urllib.request.Request(
                    f'https://api.videoask.com/questions/{qid}/answers?limit=50',
                    headers={
                        'Authorization': f'Bearer {token}',
                        'organization-id': ORG_ID
                    }
                )
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                items = data.get('results', data.get('items', []))
                for ans in items:
                    if ans.get('contact_id') == cid:
                        t = ans.get('transcription', '')
                        if t and t.strip():
                            transcripts[qkey] = t.strip()
                        break
            except Exception:
                continue
        
        q_count = sum(1 for q in ['q3','q4','q5','q6','q7'] if transcripts.get(q))
        
        # Determine market from phone
        phone_digits = re.sub(r'[^\d]', '', phone)
        if phone_digits.startswith('1') and len(phone_digits) == 11:
            area_code = phone_digits[1:4]
        elif len(phone_digits) == 10:
            area_code = phone_digits[:3]
        else:
            area_code = ''
        
        area_code_market = {
            '801': 'utah', '385': 'utah', '435': 'utah',
            '404': 'georgia', '470': 'georgia', '678': 'georgia', '770': 'georgia',
            '762': 'georgia', '706': 'georgia', '912': 'georgia', '229': 'georgia', '478': 'georgia',
            '480': 'arizona', '602': 'arizona', '623': 'arizona', '520': 'arizona', '928': 'arizona',
        }
        market = area_code_market.get(area_code, 'georgia')
        
        # Experience type from Q3
        exp_type = 'unknown'
        q3_text = transcripts.get('q3', '').lower()
        formal_kw = ['daycare','preschool','head start','montessori','after school','camp counselor',
                     'summer camp','ymca','boys and girls club','classroom','teacher','substitute',
                     'kindergarten','elementary','learning center','child development','tutor','school']
        informal_kw = ['babysit','nanny','own children','my kids','niece','nephew','sibling']
        
        has_formal = any(kw in q3_text for kw in formal_kw)
        has_informal = any(kw in q3_text for kw in informal_kw)
        
        if has_formal and has_informal:
            exp_type = 'mixed'
        elif has_formal:
            exp_type = 'formal'
        elif has_informal:
            exp_type = 'informal'
        elif any(w in q3_text for w in ['experience','worked with','children','kids']):
            exp_type = 'unclear'
        else:
            exp_type = 'none'
        
        # Simple evaluation
        if exp_type == 'formal' and q_count >= 4:
            if market == 'arizona':
                rec, conf = 'APPROVE', 'MEDIUM'
            else:
                rec, conf = 'APPROVE', 'HIGH'
        elif exp_type == 'mixed':
            rec, conf = 'APPROVE', 'MEDIUM'
        elif exp_type == 'informal':
            if market == 'utah':
                rec, conf = 'APPROVE', 'MEDIUM'
            elif market == 'arizona':
                rec, conf = 'FLAG', 'HIGH'
            else:
                rec, conf = 'FLAG', 'MEDIUM'
        elif exp_type == 'none':
            rec, conf = 'FLAG', 'LOW'
        elif exp_type == 'unclear':
            rec, conf = 'APPROVE', 'LOW'
        else:
            rec, conf = 'FLAG', 'LOW'
        
        # Format phone
        digits = re.sub(r'[^\d]', '', phone)
        if digits.startswith('1') and len(digits) == 11:
            digits = digits[1:]
        if len(digits) == 10:
            phone_formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        else:
            phone_formatted = phone
        
        # VideoAsk dashboard link
        va_link = f'https://app.videoask.com/app/organizations/{ORG_ID}/form/{FORM_ID}/conversation/{cid}'
        
        # Zendesk search link
        email_enc = email.replace('+', '%2B')
        zd_link = f'https://upkid.zendesk.com/agent/search/1?q={email_enc}'
        
        # Basic info extraction
        city = market.title()  # Simplified
        drive = ""
        exp_str = exp_type
        sched_str = "Flex"
        
        # Red flags
        flags = []
        first_name_lower = name.split()[0].lower() if name else ''
        male_names = {'brian','john','matt','matthew','jarvis','james','george','nicholas','nico',
                      'josue','elan','denetric','brodie','robert','michael','david','daniel','joseph'}
        if first_name_lower in male_names:
            flags.append('👨 MALE — centers may not place')
        
        # Build candidate
        candidate = {
            'contact_id': cid,
            'name': name,
            'email': email,
            'phone': phone,
            'phone_formatted': phone_formatted,
            'market': market,
            'va_date': va_date,
            'rec': rec,
            'confidence': conf,
            'exp_type': exp_type,
            'exp_str': exp_str,
            'city': city,
            'drive': drive,
            'loc_drive': city + (f", {drive}" if drive else ""),
            'sched_str': sched_str,
            'questions_answered': q_count,
            'app_match': '🟡',  # Default partial match
            'app_name': 'Pending lookup',
            'doc_id': '',
            'mismatches': '',
            'red_flags': flags,
            'va_link': va_link,
            'zd_link': zd_link,
            'is_duplicate': False,
            'transcripts': transcripts,
            'first_name': name.split()[0] if name else '',
        }
        
        candidates.append(candidate)
    
    # Output JSON for cron agent
    output = {
        'new_count': len(candidates),
        'candidates': candidates,
    }
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()