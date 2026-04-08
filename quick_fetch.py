#!/usr/bin/env python3
import json, subprocess, sys

token = json.load(open('/Users/tylerbot/credentials/videoask-token.json'))['access_token']
org = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
headers = f'Authorization: Bearer {token}'
org_header = f'organization-id: {org}'

contact_id = '42f4b787-0ad2-4586-9f02-b829535a4fb8'

# Fetch answers for Q3
qid = '4312c81f-5e50-4ee6-8ab0-0342b0cce53c'
url = f'https://api.videoask.com/questions/{qid}/answers?limit=50'
cmd = ['curl', '-s', '-H', headers, '-H', org_header, url]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print('curl error:', result.stderr)
    sys.exit(1)
data = json.loads(result.stdout)
print(f'Total answers: {len(data.get("results", []))}')
for ans in data.get('results', []):
    if ans.get('contact_id') == contact_id:
        print('Found answer:')
        print(json.dumps(ans, indent=2))
        break
else:
    print('No answer for contact', contact_id)