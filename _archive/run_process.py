#!/usr/bin/env python3
"""
Simple wrapper to run process-new-submissions.py
"""
import subprocess
import sys

def main():
    script_path = "/Users/tylerbot/.openclaw/workspace-videoask-reviewer/scripts/process-new-submissions.py"
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        timeout=60
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()