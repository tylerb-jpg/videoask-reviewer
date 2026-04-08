#!/usr/bin/env python3
import subprocess, sys, json, os, time

# Run the script with a timeout using subprocess
cmd = ['python3', '/Users/tylerbot/.openclaw/workspace-videoask-reviewer/scripts/process-new-submissions.py']

print(f"Running: {' '.join(cmd)}")
start = time.time()

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print(f"Completed in {time.time()-start:.2f}s")
    print(f"Exit code: {result.returncode}")
    print(f"Stdout length: {len(result.stdout)}")
    print(f"Stderr length: {len(result.stderr)}")
    
    if result.stdout:
        print("\n--- Stdout (first 1000 chars) ---")
        print(result.stdout[:1000])
    
    if result.stderr:
        print("\n--- Stderr (first我发现 500 chars) ---")
        print(result.stderr[:500])
        
except subprocess.TimeoutExpired:
    print(f"Timed out after 10 seconds")
except Exception as e:
    print(f"Error: {e}")