import os
import praw
from dotenv import load_dotenv
import json
import sys
import time
from prawcore.exceptions import PrawcoreException, ReadTimeout, RequestException

def get_reddit_client():
    load_dotenv()
    client_id = os.environ.get('REDDIT_CLIENT_ID')
    client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
    user_agent = os.environ.get('REDDIT_USER_AGENT')

    if not all([client_id, client_secret, user_agent]):
        print("Error: Reddit API credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT) not found in environment variables.", file=sys.stderr)
        print("Please set BLUESKY_USERNAME and BLUESKY_PASSWORD in your .env file or environment.", file=sys.stderr)
        return None

    print(f"[DEBUG] Reddit Client ID: {client_id}", file=sys.stderr)
    print(f"[DEBUG] Reddit Client Secret: {'*' * len(client_secret) if client_secret else 'None'}", file=sys.stderr)
    print(f"[DEBUG] Reddit User Agent: {user_agent}", file=sys.stderr)

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            timeout=30 # Increased timeout to 30 seconds
        )
        print("[DEBUG] Successfully initialized Reddit client.", file=sys.stderr)
        return reddit
    except Exception as e:
        print(f"[ERROR] Error initializing Reddit client: {type(e).__name__}: {e}", file=sys.stderr)
        return None

def get_subreddit_data(reddit_client, subreddit_name, max_retries=3):
    if not reddit_client:
        print("[DEBUG] Reddit client not initialized, cannot fetch subreddit data.", file=sys.stderr)
        return None

    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Attempting to fetch subreddit: r/{subreddit_name} (Attempt {attempt + 1}/{max_retries})", file=sys.stderr)
            subreddit = reddit_client.subreddit(subreddit_name)
            
            # Access a property to trigger API call and check existence
            # This will raise NotFound or Forbidden if the subreddit is invalid or inaccessible
            _ = subreddit.subscribers 
            print(f"[DEBUG] Successfully accessed subreddit r/{subreddit_name}. Subscribers: {subreddit.subscribers}", file=sys.stderr)

            # Fetch a few posts to get activity metrics
            posts = []
            print(f"[DEBUG] Fetching hot posts for r/{subreddit_name} (limit=5).", file=sys.stderr)
            for submission in subreddit.hot(limit=5):
                posts.append({
                    'title': submission.title,
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'created_utc': submission.created_utc
                })
            print(f"[DEBUG] Fetched {len(posts)} posts for r/{subreddit_name}.", file=sys.stderr)
            
            data = {
                'subreddit': subreddit_name,
                'subscribers': subreddit.subscribers,
                'active_user_count': subreddit.active_user_count,
                'posts': posts
            }
            print(f"[DEBUG] Compiled data for subreddit r/{subreddit_name}.", file=sys.stderr)
            return data
        except (ReadTimeout, RequestException) as e:
            print(f"[WARNING] ReadTimeout or RequestException for r/{subreddit_name} (Attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(2 ** attempt) # Exponential backoff
        except NotFound:
            print(f"[ERROR] Subreddit r/{subreddit_name} not found (404).", file=sys.stderr)
            return None
        except Forbidden:
            print(f"[ERROR] Access to subreddit r/{subreddit_name} is forbidden (403).", file=sys.stderr)
            return None
        except PrawcoreException as e:
            print(f"[ERROR] PrawcoreException for r/{subreddit_name}: {type(e).__name__}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error fetching data for subreddit r/{subreddit_name}: {type(e).__name__}: {e}", file=sys.stderr)
            return None
    print(f"[ERROR] Failed to fetch data for subreddit r/{subreddit_name} after {max_retries} attempts.", file=sys.stderr)
    return None

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Reddit subreddit data.")
    parser.add_argument("subreddit", help="The subreddit to search for (e.g., LearnGraph).")
    args = parser.parse_args()

    reddit = get_reddit_client()
    if reddit:
        subreddit_data = get_subreddit_data(reddit, args.subreddit)
        if subreddit_data:
            print(json.dumps(subreddit_data))
        else:
            print("[]")
