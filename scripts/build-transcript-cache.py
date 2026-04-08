#!/usr/bin/env python3
"""
Cache all VideoAsk transcripts to a local JSON file.
Run nightly to speed up cron processing (no API calls during the day).

Output: /Users/tylerbot/.openclaw/workspace-videoask-reviewer/transcript-cache.json
Format: { contact_id: { q3: "...", q4: "...", q5: "...", q6: "...", q7: "..." } }
"""
import json, subprocess, os, sys
from datetime import datetime

CREDENTIALS_DIR = '/Users/tylerbot/credentials'
WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
OUTPUT = f'{WORKSPACE}/transcript-cache.json'

QUESTION_IDS = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}


def load_token():
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    with open(token_path) as f:
        token_data = json.load(f)
    return token_data['access_token']


def refresh_token():
    oauth_path = f'{CREDENTIALS_DIR}/videoask-oauth.json'
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    if not os.path.exists(oauth_path):
        return False
    with open(oauth_path) as f:
        oauth = json.load(f)
    if not oauth.get('refresh_token'):
        return False
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', 'https://auth.videoask.com/oauth/token',
         '-H', 'Content-Type: application/json',
         '-d', json.dumps({
             'grant_type': 'refresh_token',
             'client_id': oauth.get('client_id', ''),
             'refresh_token': oauth['refresh_token'],
         })],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode == 0:
        new_token = json.loads(result.stdout)
        if 'access_token' in new_token:
            new_token['obtained_at'] = datetime.utcnow().isoformat() + 'Z'
            with open(token_path, 'w') as f:
                json.dump(new_token, f, indent=2)
            return True
    return False


def va_api(url, token):
    import re
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
    return json.loads(output), None


def main():
    print("Starting transcript cache build...", file=sys.stderr)
    
    token = load_token()
    cache = {}
    total_answers = 0
    
    for qkey, qid in QUESTION_IDS.items():
        print(f"  Fetching {qkey} answers...", file=sys.stderr)
        offset = 0
        while True:
            data, err = va_api(
                f'https://api.videoask.com/questions/{qid}/answers?limit=100&offset={offset}',
                token
            )
            if err:
                if err == 'TOKEN_EXPIRED':
                    print("  Token expired, refreshing...", file=sys.stderr)
                    if refresh_token():
                        token = load_token()
                        continue
                    else:
                        print("  Token refresh failed!", file=sys.stderr)
                        break
                break
            
            items = data.get('results', data.get('items', []))
            for ans in items:
                cid = ans.get('contact_id')
                t = ans.get('transcription', '')
                if cid and t and t.strip():
                    cache.setdefault(cid, {})[qkey] = t.strip()
                    total_answers += 1
            
            if not data.get('next') or len(items) == 0:
                break
            offset += 100
    
    with open(OUTPUT, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f"Done: {len(cache)} contacts, {total_answers} total answers cached", file=sys.stderr)
    print(f"Saved to {OUTPUT}")


if __name__ == '__main__':
    main()
