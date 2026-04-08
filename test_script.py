#!/usr/bin/env python3
import json, os, sys, subprocess
from datetime import datetime, timezone, timedelta

CREDENTIALS_DIR = '/Users/tylerbot/credentials'
token_path = f'{CREDENTIALS_DIR}/videoask-token.json'

with open(token_path) as f:
    token_data = json.load(f)

print(f"Token loaded")
print(f"Obtained at: {token_data.get('obtained_at', '')}")
print(f"Expires in: {token_data.get('expires_in', '')}")

# Check if expired
obtained = token_data.get('obtained_at', '')
expires_in = token_data.get('expires_in', 86400)
if obtained:
    obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
    expires_dt = obtained_dt + timedelta(seconds=expires_in - 300)  # 5min buffer
    now = datetime.now(timezone.utc)
    print(f"Obtained datetime: {obtained_dt}")
    print(f"Expires datetime: {expires_dt}")
    print(f"Current datetime: {now}")
    print(f"Is expired? {now > expires_dt}")
else:
    print("No obtained_at field")

# Try a simple API call
import requests
token = token_data['access_token']
headers = {
    'Authorization': f'Bearer {token}',
    'organization-id': '3f29b255-68a4-45c3-9cf7-883383e01bcc'
}
try:
    response = requests.get('https://api.videoask.com/forms/c44b53b4-ec5e-4da7-8266-3c0b327dba88/contacts?limit=1', headers=headers)
    print(f"API response status: {response.status_code}")
    if response.status_code == ongoing:
        print(f"API response: {response.text[:200]}")
except Exception as e:
    print(f"API error: {e}")