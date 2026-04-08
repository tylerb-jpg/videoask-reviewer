#!/usr/bin/env python3
import subprocess, json, os, sys

candidate_json = sys.argv[1] if len(sys.argv) > 1 else 'temp-candidates.json'
env = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

with open(candidate_json, 'r') as f:
    candidates = json.load(f)

for cand in candidates:
    print(f"Processing {cand['name']}...")
    row = [
        "FALSE",  # A Reviewed checkbox
        "FALSE",  # B Erica Approved checkbox
        cand['va_date'],
        f"{cand['app_match']} {cand['app_name']}",
        cand['market'].upper(),
        f"{'✅' if cand['rec'] == 'APPROVE' else '🟡'} {cand['confidence']}",
        f'=HYPERLINK("{cand["va_link"]}", "▶️ Watch")',
        cand['first_name'],
        cand['doc_id'],
        cand['email'],
        cand['phone_formatted'],
        f'=HYPERLINK("{cand["zd_link"]}", "🔍")',
        f"04/06 Intro Call Passed. {cand['city']}, {cand['drive']}. {cand['exp_str']}",
        f"04/06 Not Hiring — Intro Call. {cand['city']}. N/A (approved candidate)",
        cand['exp_str'],
        cand['loc_drive'],
        cand['sched_str'],
        "",  # AI summary placeholder
        "; ".join(cand['red_flags']),
        cand['transcripts']['q3'],
        cand['transcripts']['q4'],
        cand['transcripts']['q5'],
        cand['transcripts']['q6'],
        cand['transcripts']['q7']
    ]
    
    cmd = ['gws', 'sheets', 'values', 'append',
           '--params', json.dumps({
               'spreadsheetId': '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0',
               'range': 'Backlog Reviews!A:X',
               'valueInputOption': 'USER_ENTERED'
           }),
           '--json', json.dumps({'values': [row]})
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"Appended {cand['name']}")
        print(result.stdout[:200])
    else:
        print(f"Error: {result.stderr}")
        break