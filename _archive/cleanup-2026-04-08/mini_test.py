#!/usr/bin/env python3
import json, requests, sys, os
from datetime import datetime, timezone, timedelta

CREDENTIALS_DIR = '/Users/tylerbot/credentials'
token_path = f'{CREDENTIALS_DIR}/videoask-token.json'

with open(token_path) as f:
    token_data = json.load(f)

token = token_data['access_token']
org_id = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
form_id = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'

headers = {
    'Authorization': f'Bearer {token}',
    'organization-id': org_id
}

# Get just one contact to test
url = f'https://api.videoask.com/forms/{form_id}/contacts?limit=1&status=completed'
print(f"Testing API...")
response = requests.get(url, headers=headers, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    if 'results' in data:
        print(f"Results: {len(data['results'])}")
        if data['results']:
            print(f"First contact: {data['results'][0]['contact_id']}")
else:
    print(f"Error: {response.text}")

# Check BigQuery
print("\nTesting BigQuery...")
bq_creds = f'{CREDENTIALS_DIR}/bigquery-tyler-bot.json'
if os.path.exists(bq_creds):
    print(f"BigQuery creds exist")
else:
    print(f"BigQuery creds missing")

# Check sheet access
print("\nTesting Google Sheets access...")
env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
import subprocess
try:
    result = subprocess.run(['gws', '--version'], env=env, capture_output=True, text=True, timeout=5)
    print(f"gws version: {result.stdout.strip() if result.returncode == 0 else 'error'}")
except Exception as e:
    print(f"gws error: {e}")