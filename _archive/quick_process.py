#!/usr/bin/env python3
"""
Quick process for one candidate - manual version
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone, timedelta

CREDENTIALS_DIR = '/Users/tylerbot/credentials'
WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
MDT = timezone(timedelta(hours=-6))

QUESTION_IDS = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

def load_token():
    with open(f'{CREDENTIALS_DIR}/videoask-token.json') as f:
        token_data = json.load(f)
    return token_data['access_token']

def va_api(url, token):
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'organization-id': ORG_ID,
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        if e.code == 401 or e.code == 403:
            return None, 'TOKEN_EXPIRED'
        return None, f'HTTP_{e.code}'
    except Exception as e:
        return None, str(e)

def main():
    token = load_token()
    
    # Get completed contacts
    data, err = va_api(
        f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=30&status=completed',
        token
    )
    if err:
        print(f'Error fetching contacts: {err}')
        return
    
    contacts = data.get('results', [])
    print(f'Total completed contacts: {len(contacts)}')
    
    # Load state
    state_path = f'{WORKSPACE}/videoask-state.json'
    if os.path.exists(state_path):
        with open(state_path) as f:
            state = json.load(f)
        processed = set(state['processed_contacts'])
    else:
        processed = set()
    
    # Find first unprocessed
    for contact in contacts:
        cid = contact['contact_id']
        if cid in processed:
            continue
        
        email = (contact.get('email') or '').strip()
        name = (contact.get('name') or '').strip()
        phone = (contact.get('phone_number') or '').strip()
        
        print(f'\nProcessing new candidate: {cid}')
        print(f'Name: {name}')
        print(f'Email: {email}')
        print(f'Phone: {phone}')
        
        # Get transcripts for Q3-Q7
        transcripts = {}
        for qkey, qid in QUESTION_IDS.items():
            data2, err2 = va_api(
                f'https://api.videoask.com/questions/{qid}/answers?limit=50',
                token
            )
            if err2:
                continue
            items = data2.get('results', data2.get('items', []))
            for ans in items:
                if ans.get('contact_id') == cid:
                    t = ans.get('transcription', '')
                    if t and t.strip():
                        transcripts[qkey] = t.strip()
                    break
        
        print('\nTranscripts:')
        for qkey in ['q3','q4','q5','q6','q7']:
            print(f'{qkey}: {transcripts.get(qkey, "NO TRANSCRIPT")[:200]}...')
        
        # Return candidate data for cron agent
        candidate = {
            'contact_id': cid,
            'name': name,
            'email': email,
            'phone': phone,
            'transcripts': transcripts,
        }
        
        print('\nCandidate JSON:')
        print(json.dumps({'new_count': 1, 'candidates': [candidate]}, indent=2))
        return
    
    print('No new candidates found')
    print(json.dumps({'new_count': 0, 'candidates': []}))

if __name__ == '__main__':
    main()