#!/usr/bin/env python3
import os
import subprocess
import json

# Set environment variable
os.environ['GOOGLE_WORKSPACE_CLI_CONFIG_DIR'] = '/Users/tylerbot/.config/gws-write'

# Read the JSON values file
with open('danaya_append_values.json', 'r') as f:
    values_json = f.read()

# Build the command
cmd = [
    'gws', 'sheets', 'spreadsheets', 'values', 'append',
    '--params', '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0","range":"Backlog Reviews!A1:X1","valueInputOption":"USER_ENTERED"}',
    '--json', values_json
]

print("Executing command: " + ' '.join(cmd))

result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)