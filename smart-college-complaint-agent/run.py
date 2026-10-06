import os
import sys
import subprocess

# Locate the inner project directory
project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart-college-complaint-agent")
inner_run_script = os.path.join(project_dir, "run.py")

if __name__ == "__main__":
    if os.path.exists(inner_run_script):
        # Execute the inner run.py with the same python interpreter and arguments
        cmd = [sys.executable, inner_run_script] + sys.argv[1:]
        sys.exit(subprocess.call(cmd, cwd=project_dir))
    else:
        print(f"Error: Could not locate inner run.py at {inner_run_script}")
        sys.exit(1)
