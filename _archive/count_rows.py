#!/usr/bin/env python3
import subprocess, json, os

env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
cmd = [
    'gws', 'sheets', 'spreadsheets', 'values', 'get',
    '--params', '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0", "range":"Backlog Reviews!A:A"}'
]
result = subprocess.run(cmd, capture_output=True, text=True, env=env)
if result.returncode != 0:
    print("Error:", result.stderr)
    exit(1)

data = json.loads(result.stdout)
if 'values' in data:
    rows = len(data['values'])
    print(f"Rows with data in column A: {rows}")
else:
    print("No values found, sheet is empty")