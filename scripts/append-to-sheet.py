#!/usr/bin/env python3
"""
Append a candidate to the Backlog Reviews Google Sheet.
Handles correct column layout, boolean checkboxes, and HYPERLINK formulas.

Usage:
  python3 append-to-sheet.py < candidate.json
  echo '{"name":"John","email":"x@y.com",...}' | python3 append-to-sheet.py

Or pass a file:
  python3 append-to-sheet.py path/to/candidate.json
"""
import json, subprocess, os, sys

SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_NAME = 'Backlog Reviews'
GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}


def find_next_row():
    """Find the first empty row in column A (after header row 1)."""
    result = subprocess.run(
        ['gws', 'sheets', 'spreadsheets', 'values', 'get',
         '--params', json.dumps({
             'spreadsheetId': SPREADSHEET_ID,
             'range': f'{SHEET_NAME}!A2:A2000',
             'majorDimension': 'COLUMNS',
         })],
        capture_output=True, text=True, env=GWS_ENV, timeout=15
    )
    if result.returncode != 0:
        print(f"Error finding next row: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(result.stdout)
    values = data.get('values', [[]])
    # values is [[val1, val2, ...]] for columns format
    col_a = values[0] if values else []
    # Count non-empty cells
    count = sum(1 for v in col_a if v and v.strip())
    return count + 2  # +1 for header, +1 for next empty row


def append_row(candidate):
    """Append a candidate row to the sheet with correct formatting."""
    next_row = find_next_row()
    
    name = candidate.get('name', '')
    va_date = candidate.get('va_date', '')
    market = candidate.get('market', '')
    rec = candidate.get('rec', 'APPROVE')
    conf = candidate.get('confidence', 'MEDIUM')
    va_link = candidate.get('va_link', '')
    first_name = candidate.get('first_name', name.split()[0] if name else '')
    doc_id = candidate.get('doc_id', '')
    email = candidate.get('email', '')
    phone = candidate.get('phone_formatted', '')
    zd_link = candidate.get('zd_link', '')
    loc_drive = candidate.get('loc_drive', '')
    exp_str = candidate.get('exp_str', '')
    sched_str = candidate.get('sched_str', '')
    ai_summary = candidate.get('ai_summary', '')
    red_flags = ', '.join(candidate.get('red_flags', []))
    
    # Transcripts
    transcripts = candidate.get('transcripts', {})
    q3 = transcripts.get('q3', '')
    q4 = transcripts.get('q4', '')
    q5 = transcripts.get('q5', '')
    q6 = transcripts.get('q6', '')
    q7 = transcripts.get('q7', '')
    
    # Build intro call notes
    today = va_date or ''
    notes_parts = [today]
    if loc_drive:
        notes_parts.append(loc_drive)
    if exp_str:
        notes_parts.append(exp_str)
    intro_notes = ' | '.join(notes_parts)
    
    # Emoji for recommendation
    rec_emoji = '✅' if rec == 'APPROVE' else '🟡' if rec == 'FLAG' else '❌'
    rec_display = f"{rec_emoji} {rec}"
    if conf:
        rec_display += f" ({conf})"
    
    # Build the row — A through X (24 columns)
    row = [
        False,                          # A: Karen Reviewed (checkbox)
        False,                          # B: Erica Approved (checkbox)
        va_date,                        # C: Date YYYY-MM-DD
        f"🟢 {name}",                   # D: Name with emoji
        market,                         # E: Market
        rec_display,                    # F: Recommendation
        f'=HYPERLINK("{va_link}","VideoAsk")',  # G: VideoAsk link (formula)
        first_name,                     # H: First name
        doc_id,                         # I: Doc ID
        email,                          # J: Email
        phone,                          # K: Phone
        f'=HYPERLINK("{zd_link}","Zendesk")',   # L: Zendesk link (formula)
        intro_notes,                    # M: Intro call notes
        '',                             # N: Not hiring notes (empty)
        exp_str,                        # O: Experience
        loc_drive,                      # P: Location/drive
        sched_str,                      # Q: Schedule
        ai_summary,                     # R: AI summary (2 sentences)
        red_flags,                      # S: Red flags
        q3,                             # T: Q3 transcript
        q4,                             # U: Q4 transcript
        q5,                             # V: Q5 transcript
        q6,                             # W: Q6 transcript
        q7,                             # X: Q7 transcript
    ]
    
    # Write using batchUpdate with UpdateCellsRequest for proper checkbox + formula support
    # This is the ONLY way to get both checkboxes AND formulas to render correctly
    range_str = f'{SHEET_NAME}!A{next_row}:X{next_row}'
    
    # Build cell data with proper types
    cell_data = []
    for i, value in enumerate(row):
        col_letter = chr(65 + i)  # A, B, C, ...
        cell = {'userEnteredValue': {}}
        
        if isinstance(value, bool):
            # Checkboxes: booleanValue
            cell['userEnteredValue'] = {'boolValue': value}
        elif isinstance(value, str) and value.startswith('='):
            # Formulas: formulaValue
            cell['userEnteredValue'] = {'formulaValue': value}
        else:
            # Strings: stringValue
            cell['userEnteredValue'] = {'stringValue': str(value)}
        
        cell_data.append(cell)
    
    # Set checkbox data validation on columns A and B for this row
    # Using a single range covering both columns
    checkbox_validation = {
        'setDataValidation': {
            'range': {
                'sheetId': 412743935,
                'startRowIndex': next_row - 1,
                'endRowIndex': next_row,
                'startColumnIndex': 0,
                'endColumnIndex': 2,  # Columns A and B (0-indexed)
            },
            'rule': {
                'condition': {'type': 'BOOLEAN'}
            }
        }
    }
    
    request = {
        'requests': [
            checkbox_validation,
            {
                'updateCells': {
                    'range': {
                        'sheetId': 412743935,
                        'startRowIndex': next_row - 1,
                        'endRowIndex': next_row,
                        'startColumnIndex': 0,
                        'endColumnIndex': 24,
                    },
                    'rows': [{'values': cell_data}],
                    'fields': 'userEnteredValue',
                }
            }
        ]
    }
    
    result = subprocess.run(
        ['gws', 'sheets', 'spreadsheets', 'batchUpdate',
         '--params', json.dumps({'spreadsheetId': SPREADSHEET_ID}),
         '--json', json.dumps(request)],
        capture_output=True, text=True, env=GWS_ENV, timeout=20
    )
    
    if result.returncode != 0 or 'error' in result.stdout.lower():
        print(f"Error appending row {next_row}: {result.stdout[:200]}", file=sys.stderr)
        return -1
    
    # === Post-append verification ===
    # Read back the row and verify it's correct before confirming
    verify = subprocess.run(
        ['gws', 'sheets', 'spreadsheets', 'values', 'get',
         '--params', json.dumps({
             'spreadsheetId': SPREADSHEET_ID,
             'range': f'{SHEET_NAME}!A{next_row}:X{next_row}',
         })],
        capture_output=True, text=True, env=GWS_ENV, timeout=15
    )
    verified = False
    if verify.returncode == 0:
        vdata = json.loads(verify.stdout)
        vrow = vdata.get('values', [[]])[0]
        # Check: at least 15 cols, has date in C, has email in J
        if len(vrow) >= 15 and vrow[2] and vrow[9]:
            verified = True
        else:
            print(f"VERIFY FAIL row {next_row}: only {len(vrow)} cols, date=[{vrow[2] if len(vrow)>2 else '?'}], email=[{vrow[9] if len(vrow)>9 else '?'}]", file=sys.stderr)
    else:
        print(f"VERIFY FAIL row {next_row}: could not read back", file=sys.stderr)
    
    if not verified:
        # Delete the bad row
        subprocess.run(
            ['gws', 'sheets', 'spreadsheets', 'batchUpdate',
             '--params', json.dumps({'spreadsheetId': SPREADSHEET_ID}),
             '--json', json.dumps({'requests': [{'deleteDimension': {'range': {'sheetId': 412743935, 'dimension': 'ROWS', 'startIndex': next_row - 1, 'endIndex': next_row}}}]})],
            capture_output=True, text=True, env=GWS_ENV, timeout=15
        )
        print(f"VERIFY FAIL: deleted bad row {next_row}", file=sys.stderr)
        return -1
    
    print(f"Appended to row {next_row} (verified)")
    return next_row


def main():
    # Read candidate JSON from stdin or file argument
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            candidate = json.load(f)
    else:
        candidate = json.load(sys.stdin)
    
    row = append_row(candidate)
    if row == -1:
        print(json.dumps({"status": "error", "message": "Append failed verification"}))
        sys.exit(1)
    print(json.dumps({"status": "ok", "row": row}))


if __name__ == '__main__':
    main()
