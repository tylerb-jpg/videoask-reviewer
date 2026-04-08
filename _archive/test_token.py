#!/usr/bin/env python3
import json, sys, subprocess, os
from datetime import datetime, timezone, timedelta

CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'

token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
with open(token_path) as f:
    token_data = json.load(f)

print("Token data:")
print(f"  obtained_at: {token_data.get('obtained_at')}")
print(f"  expires_in: {token_data.get('expires_in')}")
print(f"  token_type: {token_data.get('token_type')}")

# Check expiration
obtained = token_data.get('obtained_at', '')
expires_in = token_data.get('expires_in', 86400)
if obtained:
    obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
    expires_dt = obtained_dt + timedelta(seconds=expires_in - 300)  # 5min buffer
    now = datetime.now(timezone.utc)
    print(f"  obtained_dt (UTC): {obtained_dt}")
    print(f"  expires_dt (UTC): {expires_dt}")
    print(f"  now (UTC): {now}")
    print(f"  is expired? {now > expires_dt}")
    
# Test API call
access_token = token_data['access_token']
print(f"\nTesting API call...")
cmd = [
    'curl', '-s',
    '-H', f'Authorization: Bearer {access_token}',
    '-H', f'organization-id: {ORG_ID}',
    'https://api.videoask.com/forms/c44b53b4-ec5e-4da7-8266-3c0b327dba88/contacts?limit=1'
]
print(' '.join(cmd[:5]) + '...')
result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
print(f"Return code: {result.returncode}")
if result.returncode == 0:
    try:
        data = json.loads(result.stdout)
        print(f"Response has {len(data.get('contacts', []))} contacts")
    except:
        print(f"Response: {result.stdout[:200]}")
else:
    print(f"Error: {result.stderr[:200]}")