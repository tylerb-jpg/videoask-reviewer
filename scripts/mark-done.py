#!/usr/bin/env python3
"""
Mark a VideoAsk contact as processed AFTER the cron agent has successfully
written them to the sheet and posted to Slack.

Usage: python3 mark-done.py <contact_id> [<contact_id2> ...]

This is the ONLY way candidates get marked as processed. The main
process-new-submissions.py script intentionally does NOT mark them —
this prevents candidates from falling through cracks if the cron agent
times out before finishing the sheet/Slack writes.
"""
import json, sys, os

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'

def main():
    if len(sys.argv) < 2:
        print("Usage: mark-done.py <contact_id> [<contact_id2> ...]", file=sys.stderr)
        sys.exit(1)
    
    contact_ids = sys.argv[1:]
    
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path) as f:
        state = json.load(f)
    
    processed = set(state.get('processed_contacts', []))
    added = []
    for cid in contact_ids:
        if cid not in processed:
            processed.add(cid)
            added.append(cid)
    
    state['processed_contacts'] = list(processed)
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(json.dumps({
        "marked": len(added),
        "contact_ids": added,
        "total_processed": len(processed)
    }))

if __name__ == '__main__':
    main()
