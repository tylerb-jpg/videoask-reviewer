#!/usr/bin/env python3
import json, datetime, subprocess, sys, os

def main():
    token_path = '/Users/tylerbot/credentials/videoask-token.json'
    try:
        with open(token_path) as f:
            token = json.load(f)
        
        # Check expiration
        obtained = datetime.datetime.fromisoformat(token['obtained_at'].replace('Z', '+00:00'))
        expires = obtained + datetime.timedelta(seconds=token['expires_in'])
        now = datetime.datetime.now(datetime.timezone.utc)
        
        if now > expires:
            print(json.dumps({'error': 'TOKEN_EXPIRED'}))
            return
        
        # Test API call
        access_token = token['access_token']
        org_id = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
        
        # Make a simple test call
        cmd = [
            'curl', '-s', '-w', '\n%{http_code}',
            f'https://api.videoask.com/forms/c44b53b4-ec5e-4da7-8266-3c0b327dba88/contacts?limit=1',
            '-H', f'Authorization: Bearer {access_token}',
            '-H', f'organization-id: {org_id}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        if '\n' in output:
            body, status = output.rsplit('\n', 1)
        else:
            body, status = output, '0'
        
        status = int(status) if status.isdigit() else 0
        
        if status == 401 or status == 403:
            print(json.dumps({'error': 'TOKEN_EXPIRED'}))
        elif status == 200:
            # Parse response
            data = json.loads(body) if body else {}
            contacts = data.get('contacts', [])
            print(json.dumps({'new_count': len(contacts), 'test': 'ok'}))
        else:
            print(json.dumps({'error': f'API_ERROR_{status}', 'body': body[:100]}))
            
    except Exception as e:
        print(json.dumps({'error': str(e), 'type': type(e).__name__}))

if __name__ == '__main__':
    main()