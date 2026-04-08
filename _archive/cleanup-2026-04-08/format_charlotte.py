#!/usr/bin/env python3
import json
import subprocess
import os

# Charlotte is on row 333 (0-indexed: 332)
row_index = 332

# Build the batch update request
batch_update = {
    "requests": [
        {
            "setDataValidation": {
                "range": {
                    "sheetId": 412743935,
                    "startRowIndex": row_index,
                    "endRowIndex": row_index + 1,
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
                    "startRowIndex": row_index,
                    "endRowIndex": row_index + 1,
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
                    "startRowIndex": row_index,
                    "endRowIndex": row_index + 1,
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

print("Batch update request:")
print(json.dumps(batch_update, indent=2))

cmd = [
    'gws', 'sheets', 'spreadsheets', 'batchUpdate',
    '--params', json.dumps({
        'spreadsheetId': '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
    }),
    '--json', json.dumps(batch_update)
]

print("Command:", " ".join(cmd))

result = subprocess.run(cmd, env={**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'})
print("Return code:", result.returncode)