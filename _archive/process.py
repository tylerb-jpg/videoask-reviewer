#!/usr/bin/env python3
import json, subprocess, os, sys, textwrap, datetime

# Load candidate data from previous output
with open('/tmp/output.json', 'r') as f:
    data = json.load(f)

candidates = data['candidates']
print(f"Processing {len(candidates)} candidates")

# Environment for gws
env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

# Get current non-empty rows count
cmd = ['gws', 'sheets', '+read', '--spreadsheet', '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0', '--range', 'Backlog Reviews!A:A']
result = subprocess.run(cmd, capture_output=True, text=True, env=env)
if result.returncode != 0:
    print(f"Error reading sheet: {result.stderr}")
    sys.exit(1)

values_data = json.loads(result.stdout)
values = values_data.get('values', [])
# Header is "Reviewed", so count rows after that
non_empty = len(values) - 1  # Exclude header
print(f"Current non-empty rows: {non_empty}")
print(f"Next row index (0-indexed): {non_empty}")
print(f"Next row number (1-indexed): {non_empty + 1}")

# Process each candidate
for i, candidate in enumerate(candidates):
    print(f"\n=== Processing candidate {i+1}: {candidate['name']} ===")
    
    # Build row values according to column layout
    # A: FALSE (Reviewed checkbox)
    # B: FALSE (Erica Approved checkbox)
    # C: va_date
    # D: app_match emoji + name
    # E: market (GA/UT/AZ)
    # F: rec emoji (✅/🟡) + confidence
    # G: =HYPERLINK("va_link", "▶️ Watch")
    # H: first_name
    # I: doc_id
    # J: email
    # K: phone_formatted
    # L: =HYPERLINK("zd_link", "🔍")
    # M: =TEXT(TODAY(),"MM/DD") & " Intro Call Passed. " & location + experience + schedule
    # N: =TEXT(TODAY(),"MM/DD") & " Not Hiring — Intro Call. " & location + specific denial reason
    # O: exp_str
    # P: loc_drive
    # Q: sched_str
    # R: YOUR AI SUMMARY (the 2-3 sentence assessment you wrote)
    # S: red_flags joined by semicolons
    # T-X: transcripts q3-q7
    
    # Generate AI summary based on transcripts
    transcripts = candidate['transcripts']
    
    if candidate['name'] == 'sharnise ford':
        ai_summary = """Sharnise has a strong formal background in early childhood, works in a daycare setting, and is CPR/first aid certified. She emphasizes safety and learning through play, and enjoys making a positive impact during children's key development stages. Solid Georgia candidate with a 25-mile drive radius, part-time availability, and straightforward conflict resolution approach."""
    elif candidate['name'] == 'Megan Kolodjay':
        ai_summary = """Megan has 10 years of formal childcare experience in licensed facilities, including roles as lead teacher, assistant director, and assistant teacher. She works with all ages (infant through 12), handles curriculum, cash, and classroom management. Lives in Phoenix, AZ with a 30-45 minute commute radius and is available part-time M-F 7:45am-3:30pm with potential for full-time later. Highly qualified Arizona candidate with thoughtful conflict resolution and strong passion for childcare."""
    else:
        # Generic fallback
        ai_summary = f"{candidate['name']} has {candidate['exp_str']} experience. Located in {candidate['loc_drive']}. Available {candidate['sched_str']}."
    
    # Build approved note for column M
    today = datetime.date.today().strftime("%m/%d")
    approved_note = f'{today} Intro Call Passed. {candidate["loc_drive"]}. {candidate["exp_str"]}. {candidate["sched_str"]}.'
    
    # Build denied note for column N (only if FLAG, otherwise empty)
    if candidate['rec'] == 'APPROVE':
        # For approve candidates, we still need a denial note template in case Erica denies
        denied_note = f'{today} Not Hiring — Intro Call. {candidate["loc_drive"]}. No formal experience (market requires formal childcare).'
    else:
        denied_note = f'{today} Not Hiring — Intro Call. {candidate["loc_drive"]}. Only informal experience (market requires formal childcare).'
    
    row_values = [
        False,  # A: Reviewed checkbox
        False,  # B: Erica Approved checkbox
        candidate['va_date'],  # C
        f"{candidate['app_match']} {candidate['app_name']}",  # D
        candidate['market'].upper(),  # E
        f"{'✅' if candidate['rec'] == 'APPROVE' else '🟡'} {candidate['confidence']}",  # F
        f'=HYPERLINK("{candidate["va_link"]}", "▶️ Watch")',  # G
        candidate['first_name'],  # H
        candidate['doc_id'],  # I
        candidate['email'],  # J
        candidate['phone_formatted'],  # K
        f'=HYPERLINK("{candidate["zd_link"]}", "🔍")',  # L
        f'="{approved_note}"',  # M - Use formula or plain text?
        f'="{denied_note}"',  # N
        candidate['exp_str'],  # O
        candidate['loc_drive'],  # P
        candidate['sched_str'],  # Q
        ai_summary,  # R
        "; ".join(candidate['red_flags']) if candidate['red_flags'] else "",  # S
        transcripts.get('q3', ''),  # T
        transcripts.get('q4', ''),  # U
        transcripts.get('q5', ''),  # V
        transcripts.get('q6', ''),  # W
        transcripts.get('q7', ''),  # X
    ]
    
    print(f"Row values length: {len(row_values)}")
    
    # Append row
    cmd = ['gws', 'sheets', '+append', '--spreadsheet', '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0', '--range', 'Backlog Reviews!A:X', '--values', json.dumps([row_values])]
    print(f"Running append command...")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Append failed: {result.stderr}")
        sys.exit(1)
    
    print(f"Append successful: {result.stdout[:100]}...")
    
    # Apply formatting via batchUpdate
    sheet_id = 412743935  # From earlier
    row_index = non_empty + i  # 0-indexed
    
    # Determine row color based on rec + confidence
    if candidate['rec'] == 'APPROVE':
        if candidate['confidence'] == 'HIGH':
            color = {'red': 0.85, 'green': 0.95, 'blue': 0.85}
        elif candidate['confidence'] == 'MEDIUM':
            color = {'red': 0.95, 'green': 0.98, 'blue': 0.88}
        else:  # LOW
            color = {'red':的特1.0, 'green': 1.0, 'blue': 0.88}
    else:  # FLAG
        if candidate['confidence'] == 'HIGH':
            color = {'red': 1.0, 'green': 0.8, 'blue': 0.8}
        elif candidate['confidence'] == 'MEDIUM':
            color = {'red': 1.0, 'green': 0.88, 'blue': 0.82}
        else:  # LOW
            color = {'red': 1.0, 'green': 0.9, 'blue': 0.85}
    
    batch_update = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_index,
                        "endRowIndex": row_index + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 2
                    },
                    "rule": {
                        "condition": { "type": "BOOLEAN" },
                        "showCustomUi": true
                    }
                }
            },
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_index,
                        "endRowIndex": row_index + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 2
                    },
                    "cell": {
                        "userEnteredValue": { "boolValue": false }
                    },
                    "fields": "userEnteredValue"
                }
            },
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_index,
                        "endRowIndex": row_index + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": XVI24
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.85, "green": 0.95, "blue": 0.85}
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor"
                }
            }
        ]
    }
    
    cmd = ['gws', 'sheets', 'spreadsheets', 'batchUpdate', '--params', json.dumps({"spreadsheetId": "1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0"}), '--json', json.dumps(batch_update)]
    print(f"Applying formatting...")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Formatting failed: {result.stderr}")
        sys.exit(1)
    
    print(f"Formatting applied successfully")
    
    # Post to Slack
    slack_message = f"""✅ {candidate['rec']} ({candidate['confidence']}) — {candidate['name']} | {candidate['market'].upper()} | {candidate['va_date']}
{ai_summary[:100]}...
→ View in sheet: https://docs.google.com/spreadsheets/d/1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0/edit"""
    
    print(f"Slack message (would be posted to C0AQQ2LBTKJ):")
    print(slack_message)
    
    # Mark as processed
    print(f"Would mark as processed with mark-done.py {candidate['contact_id']}")
    
    # Update non_empty count for next iteration
    non_empty += 1

print(f"\n=== Processing complete ===")
print(f"Processed {len(candidates)} candidates")