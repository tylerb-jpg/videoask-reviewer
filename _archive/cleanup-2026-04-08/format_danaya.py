#!/usr/bin/env python3
import os
import subprocess
import json

# Set environment variable
os.environ['GOOGLE_WORKSPACE_CLI_CONFIG_DIR'] = '/Users/tylerbot/.config/gws-write'

# Build the batch update request
request_data = {
    "spreadsheetId": "1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0",
    "requests": [
        {
            "setDataValidation": {
                "range": {
                    "sheetId": 412743935,
                    "startRowIndex": 334,
                    "endRowIndex": 335,
                    "startColumnIndex": 0,
                    "endColumnIndex": 2
                },
                "rule": {
                    "condition": { "type": "BOOLEAN" },
                    "showCustomUi": True
                }
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": 412743935,
                    "startRowIndex": 334,
                    "endRowIndex": 335,
                    "startColumnIndex": 0,
                    "endColumnIndex": 2
                },
                "cell": {
                    "userEnteredValue": { "boolValue": False }
                },
                "fields": "userEnteredValue"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": 412743935,
                    "startRowIndex": 334,
                    "endRowIndex": 335,
                    "startColumnIndex": 0,
                    "endColumnIndex": 24
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": { "red": 0.95, "green": 0.98, "blue": 0.88 }
                    }
                },
                "fields": "userEnteredFormat.backgroundColor"
            }
        }
    ]
}

# Write to a temporary file
with open('/tmp/danaya_format.json', 'w') as f:
    json.dump(request_data, f)

# Build the command
cmd = [
    'gws', 'sheets', 'spreadsheets', 'batchUpdate',
    '--params', '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0"}',
    '--json', '@/tmp/danaya_format.json'
]

print("Executing command: " + ' '.join(cmd))

result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)