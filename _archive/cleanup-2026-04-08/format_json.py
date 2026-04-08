#!/usr/bin/env python3
import os
import subprocess

# Set environment variable
os.environ['GOOGLE_WORKSPACE_CLI_CONFIG_DIR'] = '/Users/tylerbot/.config/gws-write'

# Create the JSON request for the body
json_request = '{"requests":[{"setDataValidation":{"range":{"sheetId":412743935,"startRowIndex":334,"endRowIndex":335,"startColumnIndex":0,"endColumnIndex":2},"rule":{"condition":{"type":"BOOLEAN"},"showCustomUi":true}}},{"repeatCell":{"range":{"sheetId":412743935,"startRowIndex":334,"endRowIndex":335,"startColumnIndex":0,"endColumnIndex":2},"cell":{"userEnteredValue":{"boolValue":false}},"fields":"userEnteredValue"}},{"repeatCell":{"range":{"sheetId":412743935,"startRowIndex":334,"endRowIndex":335,"startColumnIndex":0,"endColumnIndex":24},"cell":{"userEnteredFormat":{"backgroundColor":{"red":0.95,"green":0.98,"blue":0.88}}},"fields":"userEnteredFormat.backgroundColor"}}]}'

# Build the command
cmd = [
    'gws', 'sheets', 'spreadsheets', 'batchUpdate',
    '--params', '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0"}',
    '--json', json_request
]

print("Executing command: " + ' '.join(cmd))

result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)