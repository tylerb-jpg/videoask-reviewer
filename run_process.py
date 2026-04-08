#!/usr/bin/env python3
import sys, os, subprocess, json

# Add workspace to path
sys.path.insert(0, '/Users/tylerbot/.openclaw/workspace-videoask-reviewer')

# Try to import the module
try:
    # The script is not a module, so we need to run it directly
    cmd = ['python3', '/Users/tylerbot/.openclaw/workspace-videoask-reviewer/scripts/process-new-submissions.py']
    
    # Run with timeout using subprocess
    import signal
    
    class TimeoutException(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutException("Timeout")
    
    # Set timeout to 30 seconds
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        signal.alarm(0)  # Cancel alarm
        
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("Output:")
            try:
                data = json.loads(result.stdout)
                print(json.dumps(data, indent=2))
            except:
                print(result.stdout[:1000])
        if result.stderr:
            print("Stderr:", result.stderr[:500])
            
    except TimeoutException:
        print("Script timed out after 30 seconds")
        signal.alarm(0)
    except Exception as e:
        print(f"Error running script: {e}")
        
except Exception as e:
    print(f"Setup error: {e}")