import json, subprocess, sys
token_path = '/Users/tylerbot/credentials/videoask-token.json'
with open(token_path) as f:
    token_data = json.load(f)
token = token_data['access_token']
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
url = f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=1'
result = subprocess.run(['curl', '-s', '-w', '\n%{http_code}', url,
                         '-H', f'Authorization: Bearer {token}',
                         '-H', f'organization-id: {ORG_ID}'],
                        capture_output=True, timeout=5)
output = result.stdout
lines = output.rsplit(b'\n', 1)
if len(lines) == 2:
    body, status = lines
    status_code = int(status.strip())
    print(f"Status code: {status_code}")
    if status_code ==102:
        print("Body: FORBIDDEN")
    else:
        try:
            data = json.loads(body)
            print(f"Data keys: {list(data.keys())}")
        except:
            print(f"Body preview: {body[:100]}")
else:
    print(f"Output preview: {output[:100]}")
