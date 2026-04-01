#!/usr/bin/env python3
"""
Generate AI-quality summaries for all 217 candidates by processing
transcripts through Claude, then updating the Google Sheet.
Run via: claude --permission-mode bypassPermissions --print "python3 scripts/generate-ai-summaries.py"
"""
import json, subprocess, os, sys, time

SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}

def update_sheet_column(col, start_row, values):
    """Write a list of [value] rows to a column."""
    end_row = start_row + len(values) - 1
    result = subprocess.run(
        ['gws', 'sheets', 'spreadsheets', 'values', 'update',
         '--params', json.dumps({
             'spreadsheetId': SPREADSHEET_ID,
             'range': f'Backlog Reviews!{col}{start_row}:{col}{end_row}',
             'valueInputOption': 'USER_ENTERED'
         }),
         '--json', json.dumps({'values': values})],
        capture_output=True, text=True, env=GWS_ENV
    )
    return result.returncode == 0

def main():
    evals = json.load(open('/Users/tylerbot/.openclaw/workspace-videoask-reviewer/va-evaluations-cache.json'))
    evals_sorted = list(reversed(evals))  # oldest first
    
    print(f"Processing {len(evals_sorted)} candidates for AI summaries...")
    
    # Process in batches of 10 for efficiency
    BATCH_SIZE = 10
    all_summaries = []
    
    for batch_start in range(0, len(evals_sorted), BATCH_SIZE):
        batch = evals_sorted[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(evals_sorted) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n=== Batch {batch_num}/{total_batches} ===")
        
        # Build prompt for this batch
        candidates_text = ""
        for i, e in enumerate(batch):
            q3 = (e.get('q3') or 'No transcript')[:600]
            q4 = (e.get('q4') or 'Not stated')[:300]
            q5 = (e.get('q5') or 'Not stated')[:300]
            q6 = (e.get('q6') or 'Not answered')[:400]
            q7 = (e.get('q7') or 'Not answered')[:300]
            
            candidates_text += f"""
---
CANDIDATE {batch_start + i + 1}: {e['name']}
Market: {e['market'].title()} | Rec: {e['recommendation']} ({e['confidence']}) | Questions: {e['questions_answered']}/5
Q3 (Experience): {q3}
Q4 (Location): {q4}
Q5 (Schedule): {q5}
Q6 (Conflict): {q6}
Q7 (Why Great): {q7}
"""
        
        prompt = f"""You are evaluating teacher candidates for Upkid, a childcare staffing platform. Write a 2-3 sentence summary for each candidate below.

Rules:
- Be specific — reference what they actually said, not generic labels
- Be opinionated — "strong candidate", "judgment call", "thin profile"  
- Compare to market criteria: Arizona requires 6mo formal, Georgia prefers formal, Utah is lenient
- Flag concerns: out-of-market location, no experience, garbled transcript, male candidate
- Mention standout details: grew up in daycare, pursuing education degree, Head Start experience, etc.
- Keep each summary to 2-3 sentences max

Output ONLY a JSON array of objects with "candidate_number" and "summary" fields. No other text.

{candidates_text}"""

        # Call Claude API via the claude CLI
        result = subprocess.run(
            ['claude', '--permission-mode', 'bypassPermissions', '--print', '-p', prompt],
            capture_output=True, text=True, timeout=120,
            cwd='/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
        )
        
        if result.returncode != 0:
            print(f"  Error in batch {batch_num}: {result.stderr[:200]}")
            # Fill with placeholder
            for e in batch:
                all_summaries.append([f"{e['recommendation']} ({e['confidence']})"])
            continue
        
        # Parse response
        output = result.stdout.strip()
        # Find JSON array in response
        try:
            # Try to find JSON array
            start_idx = output.find('[')
            end_idx = output.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = output[start_idx:end_idx]
                summaries = json.loads(json_str)
                
                for s in summaries:
                    all_summaries.append([s.get('summary', 'See transcript')])
                
                print(f"  Got {len(summaries)} summaries")
                # Preview first one
                if summaries:
                    print(f"  Sample: {summaries[0].get('summary', '')[:100]}...")
            else:
                print(f"  No JSON found in response, using fallback")
                for e in batch:
                    all_summaries.append([f"{e['recommendation']} ({e['confidence']})"])
        except json.JSONDecodeError as ex:
            print(f"  JSON parse error: {ex}")
            for e in batch:
                all_summaries.append([f"{e['recommendation']} ({e['confidence']})"])
        
        # Update sheet every batch so progress is visible
        if all_summaries:
            update_sheet_column('Q', 2, all_summaries)
            print(f"  Sheet updated with {len(all_summaries)} summaries so far")
        
        # Small delay to avoid rate limits
        time.sleep(1)
    
    print(f"\nDone! {len(all_summaries)} summaries written to sheet")

if __name__ == '__main__':
    main()
