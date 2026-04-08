#!/usr/bin/env python3
"""Backfill Zendesk Note (M) and Summary (R) for all existing rows using transcript data."""

import subprocess
import json
import sys
import os

SHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_NAME = 'Backlog Reviews'
GRID_ID = 412743935  # from earlier discovery

def gws(*args):
    result = subprocess.run(
        ['gws', 'sheets', *args],
        capture_output=True, text=True, timeout=30,
        env={**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': os.path.expanduser('~/.config/gws-write')}
    )
    if result.returncode != 0:
        print(f"gws error: {result.stderr}", file=sys.stderr)
        return None
    return json.loads(result.stdout)

def clean_transcript(text):
    if not text:
        return ''
    t = text.replace('\n', ' ').replace('  ', ' ')
    for artifact in [' um ', ' uh ', ' like ', ' you know ', ' basically ', ' honestly ']:
        t = t.replace(artifact, ' ')
    return t.strip()

def build_zendesk_note(row):
    """Build zendesk note from row data. Columns: C=date, D=name, E=market, T=q3, V=q5, W=q6, X=q7, P=loc_drive, Q=sched"""
    def get(col_idx):
        return row[col_idx] if col_idx < len(row) else ''
    
    va_date = get(2)   # C
    name = get(3)      # D
    market = get(4)    # E
    q3 = get(19)       # T
    q5 = get(21)       # V
    q6 = get(22)       # W
    q7 = get(23)       # X
    city_drive = get(15)  # P
    sched = get(16)    # Q
    
    parts = []
    parts.append(f"{va_date} VideoAsk intro passed. {name} ({market}).")
    
    if q3:
        q3_clean = clean_transcript(q3)
        sentences = [s.strip() for s in q3_clean.split('.') if s.strip() and len(s.strip()) > 10]
        exp_text = '. '.join(sentences[:3]).strip()
        if len(exp_text) > 300:
            exp_text = exp_text[:297] + '...'
        if exp_text:
            parts.append(exp_text)
    
    if city_drive:
        parts.append(f"Located in {city_drive}.")
    
    if sched:
        parts.append(f"Availability: {sched}.")
    
    if q6:
        q6_clean = clean_transcript(q6)
        q6_sent = [s.strip() for s in q6_clean.split('.') if s.strip() and len(s.strip()) > 15]
        if q6_sent:
            cr = q6_sent[0][:200]
            if len(q6_sent[0]) > 200:
                cr = cr[:197] + '...'
            parts.append(f"Conflict resolution approach: {cr}.")
    
    if q7:
        q7_clean = clean_transcript(q7)
        q7_sent = [s.strip() for s in q7_clean.split('.') if s.strip() and len(s.strip()) > 15]
        why_text = '. '.join(q7_sent[:2]).strip()
        if len(why_text) > 250:
            why_text = why_text[:247] + '...'
        if why_text:
            parts.append(f"Why they'd be a great fit: {why_text}.")
    
    return ' '.join(parts)

def build_summary(row):
    """Build short summary for column R."""
    def get(col_idx):
        return row[col_idx] if col_idx < len(row) else ''
    
    rec = get(5)       # F
    exp = get(14)      # O
    loc = get(15)      # P
    sched = get(16)    # Q
    
    summary = f"{rec} — {exp}"
    if loc:
        summary += f" | {loc}"
    if sched:
        summary += f" | {sched}"
    return summary

def main():
    # Step 1: Read all data rows (skip header row 1)
    print("Reading sheet data...", file=sys.stderr)
    result = gws('spreadsheets', 'values', 'get',
                 '--params', json.dumps({
                     'spreadsheetId': SHEET_ID,
                     'range': f'{SHEET_NAME}!A2:X'
                 }))
    if not result:
        print("Failed to read sheet", file=sys.stderr)
        sys.exit(1)
    
    rows = result.get('values', [])
    print(f"Found {len(rows)} data rows", file=sys.stderr)
    
    if not rows:
        print("No rows to update")
        return
    
    # Step 2: Build updates for each row
    updates = []  # (row_number, zendesk_note, summary)
    skipped = 0
    
    for i, row in enumerate(rows):
        row_num = i + 2  # +2 because sheet is 1-indexed and we skipped header
        
        # Skip if no name (empty row)
        if len(row) < 4 or not row[3]:
            skipped += 1
            continue
        
        # Check if Q7 exists (transcript data available)
        has_transcripts = len(row) > 23 and row[23]
        
        zendesk_note = build_zendesk_note(row) if has_transcripts else row[12] if len(row) > 12 else ''
        summary = build_summary(row)
        
        updates.append((row_num, zendesk_note, summary))
    
    print(f"Updating {len(updates)} rows ({skipped} empty skipped)", file=sys.stderr)
    
    # Step 3: Batch update using batchUpdate
    # Update in chunks of 100 to stay within API limits
    CHUNK = 100
    total_updated = 0
    
    for chunk_start in range(0, len(updates), CHUNK):
        chunk = updates[chunk_start:chunk_start + CHUNK]
        requests = []
        
        for row_num, zendesk_note, summary in chunk:
            # Column M (index 12) = zendesk note
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': GRID_ID,
                        'startRowIndex': row_num - 1,
                        'endRowIndex': row_num,
                        'startColumnIndex': 12,
                        'endColumnIndex': 13,
                    },
                    'rows': [{'values': [{'userEnteredValue': {'stringValue': zendesk_note}}]}],
                    'fields': 'userEnteredValue',
                }
            })
            # Column R (index 17) = summary
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': GRID_ID,
                        'startRowIndex': row_num - 1,
                        'endRowIndex': row_num,
                        'startColumnIndex': 17,
                        'endColumnIndex': 18,
                    },
                    'rows': [{'values': [{'userEnteredValue': {'stringValue': summary}}]}],
                    'fields': 'userEnteredValue',
                }
            })
        
        result = gws('spreadsheets', 'batchUpdate',
                     '--params', json.dumps({'spreadsheetId': SHEET_ID}),
                     '--json', json.dumps({'requests': requests}))
        
        if result:
            total_updated += len(chunk)
            print(f"Updated rows {chunk_start + 1}-{chunk_start + len(chunk)}", file=sys.stderr)
        else:
            print(f"Failed to update chunk starting at {chunk_start}", file=sys.stderr)
    
    print(f"Done. Updated {total_updated} rows.")

if __name__ == '__main__':
    main()
