#!/usr/bin/env python3
import json
import os

# Load state
state_path = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer/videoask-state.json'
with open(state_path) as f:
    state = json.load(f)

processed = set(state['processed_contacts'])
print(f"Processed: {len(processed)} contacts")

# Check if any of the recent contacts are already processed
recent = [
    "42f4b787-0ad2-4586-9f02-b829535a4fb8",
    "5eebcb52-736a-4a63-9137-2683eeda7d11",
    "c5a30b19-bf65-4090-b35b-3d96aaab9f88",
    "39b69639-86f7-4294-a48e-c74bdd2fa0bf",
    "2500bee3-3621-4d35-a39b-272095d4e387",
    "123209cf-df57-4344-9bda-0a09e58c7e84",
    "1b26a46e-b884-418b-8921-df780d8e6e50",
    "7c781279-f626-46df-aaf6-e4ae23318580",
    "175b9576-8cd5-4c9d-bbc4-85fa0f6abc7f",
    "597d81d4-6826-47e4-a1f9-90731dc0560f"
]

for c in recent:
    if c in processed:
        print(f"✓ {c} already processed")
    else:
        print(f"✗ {c} NOT processed")

print(f"\nLast run: {state.get('last_run', 'unknown')}")