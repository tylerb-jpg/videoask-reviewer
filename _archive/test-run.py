#!/usr/bin/env python3
import subprocess
import sys
import os

os.chdir('/Users/tylerbot/.openclaw/workspace-videoask-reviewer')
result = subprocess.run([sys.executable, 'scripts/process-new-submissions.py'], 
                       capture_output=True, text=True, timeout=30)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)