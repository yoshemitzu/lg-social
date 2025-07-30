import os
import subprocess
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
scraper_path = os.path.join(script_dir, 'reddit_scraper.py')

# Use a known subreddit that should exist, e.g., 'Python' or 'AskReddit'
subreddit_to_test = "Python"

command = [sys.executable, scraper_path, subreddit_to_test]

print(f"[DEBUG] Testing Reddit scraper with subreddit: r/{subreddit_to_test}", file=sys.stderr)
print(f"[DEBUG] Command: {' '.join(command)}", file=sys.stderr)

env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

try:
    process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=False, env=env)
    
    print("--- STDOUT ---")
    print(process.stdout)
    print("--- STDERR ---")
    print(process.stderr)
    print(f"--- EXIT CODE: {process.returncode} ---")

except Exception as e:
    print(f"[ERROR] Error running test script: {e}", file=sys.stderr)
