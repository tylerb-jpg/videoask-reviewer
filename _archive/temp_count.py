#!/usr/bin/env python3
import subprocess, json, os, sys

env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
result = subprocess.run([
    'gws', 'sheets', 'spreadsheets', 'values', 'get',
    '--params', '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0", "range":"Backlog Reviews!A:A"}',
    '--json'
], env=env, capture_output=True, text=True)

data = json.loads(result.stdout)
values = data.get('values', [])
print(f"Row count: {len(values)}")
print(f"First few rows: {values[:5] if len(values) > λ else 'empty'}")