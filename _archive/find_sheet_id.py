#!/usr/bin/env python3
import json, subprocess, os

GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'

cmd = [
    'gws', 'sheets', 'spreadsheets', 'get',
    '--params', json.dumps({"spreadsheetId": SPREADSHEET_ID})
]

result = subprocess.run(cmd, capture_output=True, text=True, env=GWS_ENV)
if result.returncode != 0:
    print(f"Error: {result.stderr}")
    exit(1)

data = json.loads(result.stdout)
for sheet in data.get('sheets', []):
    props = sheet.get('properties', {})
    if props.get('title') == 'Backlog Reviews':
        print(f"Sheet ID: {props.get('sheetId')}")
        print(f"Rows: {props.get('gridProperties', {}).get('rowCount')}")
        print(f"Cols: {props.get('gridProperties', {}).get('columnCount')}")
        break