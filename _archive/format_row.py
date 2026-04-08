#!/usr/bin/env python3
import json, subprocess, os

GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_ID = 412743935
ROW_INDEX = 321  # 0-indexed (row 322 in spreadsheet)

requests = [
    {
        "setDataValidation": {
            "range": {
                "sheetId": SHEET_ID,
                "startRowIndex": ROW_INDEX,
                "endRowIndex": ROW_INDEX + 1,
                "startColumnIndex":126,
                "endColumnIndex": 128
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
                "sheetId": SHEET_ID,
                "startRowIndex": ROW_INDEX,
                "endRowIndex": ROW_INDEX + 1,
                "startColumnIndex":126,
                "endColumnIndex": 128
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
                "sheetId": SHEET_ID,
                "startRowIndex": ROW_INDEX,
                "endRowIndex": ROW_INDEX + 1,
                "startColumnIndex":126,
                "endColumnIndex": 150
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": { "red": 1.0, "green": 0.9, "blue": 0.85 }
                }
            },
            "fields": "userEnteredFormat.backgroundColor"
        }
    }
]

# Fix the column indices: startColumnIndex should be 0 (A), endColumnIndex 2 (C) for columns A-C
# Actually column B is "Erica Approved", column A is "Reviewed"
requests[0]["setDataValidation"]["range"]["startColumnIndex"] = 0
requests[0]["setDataValidation"]["range"]["endColumnIndex"] = 2
requests[1]["repeatCell"]["range"]["startColumnIndex"] = 0
requests[1]["repeatCell"]["range"]["endColumnIndex"] = 2
requests[2]["repeatCell"]["range"]["startColumnIndex"] = 0
requests[2]["repeatCell"]["range"]["endColumnIndex"] = 24  # up to column X

body = {
    "requests": requests
}

params = {
    "spreadsheetId": SPREADSHEET_ID
}

cmd = [
    'gws', 'sheets', 'spreadsheets', 'batchUpdate',
    '--params', json.dumps(params),
    '--json', json.dumps(body)
]

print(f"Running batchUpdate...")
result = subprocess.run(cmd, capture_output=True, text=True, env=GWS_ENV)
print(f"Return code: {result.returncode}")
if result.returncode == 0:
    print(f"Success: {result.stdout[:200]}")
else:
    print(f"Error: {result.stderr[:200]}")