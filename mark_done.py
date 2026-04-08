#!/usr/bin/env python3
"""
Mark a VideoAsk contact as processed in state.json.
Called after successful sheet + Slack writes.
"""
import json, sys, os

WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mark-done.py <contact_id>")
        sys.exit(1)
    
    contact_id = sys.argv[1]
    state_path = f'{WORKSPACE}/videoask-state.json'
    
    with open(state_path) as f:
        state = json.load(f)
    
    if contact_id not in state['processed_contacts']:
        state['processed_contacts'].append(contact_id)
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"Marked {contact_id} as processed")
    else:
        print(f"Contact {contact_id} already processed")

if __name__ == '__main__':
    main()