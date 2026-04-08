import json, subprocess
token_path = '/Users/tylerbot/credentials/videoask-token.json'
with open(token_path) as f:
    token_data = json.load(f)
token = token_data['access_token']
print(f"Token length: {len(token)}")
print(f"Token expires_in: {token_data['expires_in']}")
print(f"Token obtained_at: {token_data['obtained_at']}")
# Simple test API call
result = subprocess.run(['curl', '-s', '-w', '\n%{http_code}', 
                         'https://api.videoask.com/forms/c44b53b4-ec5e-4da7-8266-3c0b327dba88/contacts?limit=1',
                         '-H', f'Authorization: Bearer {token}',
                         '-H', 'organization-id: 3f29b255-68a4-45c3-9cf7-883383e01bcc'],
                        capture_output=True, timeout=5)
print(f"Curl return code: {result.returncode}")
print(f"Stdout length: {len(result.stdout)}")
print(f"Stderr: {result.stderr}")
