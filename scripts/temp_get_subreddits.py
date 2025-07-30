import csv
import os
import subprocess
import json
import sys

def get_valid_subreddits(csv_path):
    valid_subreddits = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scraper_path = os.path.join(script_dir, 'reddit_scraper.py')

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # Skip header
        for row in reader:
            if row:
                hashtag = row[0].lstrip('#')
                subreddit_name = hashtag # Assuming subreddit name is the hashtag without '#'

                command = [sys.executable, scraper_path, subreddit_name]
                
                try:
                    process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=False)
                    
                    is_valid = True
                    # Check for specific error messages in stderr
                    if "404 HTTP response" in process.stderr or \
                       "Redirect: Redirect to /subreddits/search" in process.stderr or \
                       "Forbidden: received 403 HTTP response" in process.stderr:
                        is_valid = False
                    
                    # If stderr is clean, check stdout for valid JSON data
                    if is_valid and process.stdout.strip() and process.stdout.strip() != "[]":
                        try:
                            json_output = json.loads(process.stdout)
                            if not json_output: # If JSON is empty, consider it invalid for this purpose
                                is_valid = False
                        except json.JSONDecodeError:
                            # Not valid JSON, likely an unexpected error from scraper, so consider invalid
                            is_valid = False
                    elif is_valid: # If stdout is empty or "[]", and no stderr errors, it's still valid (just no posts)
                        pass # Subreddit exists, but no posts found, still a valid subreddit.

                    if is_valid:
                        valid_subreddits.append(subreddit_name)
                    else:
                        print(f"Excluding r/{subreddit_name} due to invalid response.", file=sys.stderr)

                    if process.stderr:
                        print(f"Stderr for {subreddit_name}: {process.stderr}", file=sys.stderr)

                except Exception as e:
                    print(f"Error running scraper for {subreddit_name}: {e}", file=sys.stderr)
    return valid_subreddits

csv_file_path = "C:\\Users\\yoshe\\Dropbox\\Obsidian\\main-vault\\main-vault\\LearnGraph\\data\\HashtagLinks.csv"
subreddits = get_valid_subreddits(csv_file_path)
print(",".join(subreddits))
