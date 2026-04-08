#!/usr/bin/env python3
import json, subprocess, sys, os

def main():
    # Load token
    token_path = '/Users/tylerbot/credentials/videoask-token.json'
    with open(token_path) as f:
        token_data = json.load(f)
    token = token_data['access_token']
    org_id = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
    form_id = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
    
    # Get contacts
    cmd = ['curl', '-s', '-H', f'Authorization: Bearer {token}', '-H', f'organization-id: {org_id}', f'https://api.videoask.com/forms/{form_id}/contacts?limit=100']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f'Error: {result.stderr}', file=sys.stderr)
        sys.exit(1)
    
    data = json.loads(result.stdout)
    completed = [c for c in data.get('results', []) if c.get('status') == 'completed']
    print(f'Found {len(completed)} completed contacts')
    
    # Load state
    state_path = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer/videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    processed = set(state['processed_contacts'])
    
    # Find new ones
    new_candidates = []
    for contact in completed[:10]:  # Limit to 10 for testing
        cid = contact.get('contact_id')
        if cid and cid not in processed:
            print(f'New candidate: {cid} - {contact.get("name")}')
            new_candidates.append(contact)
    
    print(f'Total new candidates: {len(new_candidates)}')
    
    # Get transcripts for first new candidate
    if new_candidates:
        contact = new_candidates[0]
        cid = contact['contact_id']
        
        # Get Q3 transcript
        q3_id = '4312c81f-5e50-4ee6-8ab0-0342b0cce53c'
        cmd = ['curl', '-s', '-H', f'Authorization: Bearer {token}', '-H', f'organization-id: {org_id}', f'https://api.videoask.com/questions/{q3_id}/answers?limit=50']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            answers = json.loads(result.stdout)
            for ans in answers.get('results', []):
                if ans.get('contact_id') == cid:
                    transcript = ans.get('transcription', '')
                    print(f'Q3 transcript: {transcript[:200]}...')
                    break
        
        output = {
            'new_count': len(new_candidates),
            'candidates': [{
                'contact_id': c['contact_id'],
                'name': c.get('name'),
                'email': c.get('email'),
                'phone': c.get('phone_number'),
                'created_at': c.get('created_at'),
            } for c in new_candidates[:2]]  # Max 2 per run
        }
        print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()