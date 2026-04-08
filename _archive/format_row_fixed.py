#!/usr/bin/env python3
import json, subprocess, os

SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_ID = 412743935
ROW_INDEX = 314  # 0-indexed (row 315 in sheet)
GWS_ENV = {'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

# APPROVE MEDIUM color: rgb(0.95, 0.98, 0.88)
requests = {
    "requests": [
        {
            "setDataValidation": {
                "range": {
                    "sheetId": SHEET_ID,
                    "startRowIndex": ROW_INDEX,
                    "endRowIndex": ROW_INDEX + 1,
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
                    "sheetId": SHEET_ID,
                    "startRowIndex": ROW_INDEX,
                    "endRowIndex": ROW_INDEX + 1,
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
                    "sheetId": SHEET_ID,
                    "startRowIndex": ROW_INDEX,
                    "endRowIndex": ROW_INDEX + 1,
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

cmd = [
    "gws", "sheets", "spreadsheets", "batchUpdate",
    "--params", json.dumps({"spreadsheetId": SPREADSHEET_ID}),
    "--json", json.dumps(requests)
]

print("Running batchUpdate...")
result = subprocess.run(cmd, capture_output=True, text=True, env={**GWS_ENV, **os.environ})
print("Return code:", result.returncode)
if result.stdout:
    print("Stdout:", result.stdout[:500])
if result.stderr:
    print("Stderr:", result.stderr[:500])