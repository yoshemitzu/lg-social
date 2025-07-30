import os
import argparse
from atproto import Client, models
from dotenv import load_dotenv
import json
import re # Import regex module
import sys # Import sys module



SESSION_FILE = 'bluesky_session.json'

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    return None

def save_session(session):
    with open(SESSION_FILE, 'w') as f:
        json.dump(session, f)

def clean_string(s):
    """Removes common non-printable ASCII characters from a string."""
    if s is None:
        return None
    # Use a raw string literal for the regex pattern to avoid issues with backslashes
    return re.sub(r'[^\x20-\x7E\n\r\t]', '', s)

def get_bluesky_client():
    """Initializes and returns an authenticated Bluesky client."""
    # Load environment variables from .env file
    load_dotenv()

    client = Client()
    
    # Try to load existing session
    session = load_session()
    if session:
        print("[DEBUG] Attempting to use saved session.", file=sys.stderr)
        try:
            client.login(session['identifier'], session['password'])
            # If login successful with old credentials, it means session is still valid or refreshed
            print("Successfully logged into Bluesky using saved session.", file=sys.stderr)
            return client
        except Exception as e:
            print(f"[DEBUG] Error using saved session, attempting fresh login: {type(e).__name__}: {e}", file=sys.stderr)
            # Fall through to fresh login if session fails

    username = os.environ.get('BLUESKY_USERNAME') # Directly use env var
    password = os.environ.get('BLUESKY_PASSWORD') # Directly use env var

    if not username or not password:
        print("Error: Bluesky username and password not found in environment variables.", file=sys.stderr)
        print("Please set BLUESKY_USERNAME and BLUESKY_PASSWORD in your .env file or environment.", file=sys.stderr)
        return None

    try:
        print(f"[DEBUG] Attempting fresh login with username: {username} and password: {'*' * len(password) if password else 'None'}", file=sys.stderr)
        client.login(username, password)
        save_session({'identifier': username, 'password': password}) # Save new session
        print("Successfully logged into Bluesky with fresh credentials.", file=sys.stderr)
        return client
    except Exception as e:
        print(f"Error logging into Bluesky: {type(e).__name__}: {e}", file=sys.stderr)
        return None

def search_bluesky_hashtag(client: Client, hashtag: str, limit: int = 10):
    """Searches for posts with a given hashtag on Bluesky and returns relevant data."""
    if not client:
        return []

    print(f"Searching for posts with hashtag: #{hashtag} (limit: {limit})", file=sys.stderr)
    posts_data = []
    try:
        response = client.app.bsky.feed.search_posts(params={'q': f'#{hashtag}', 'limit': limit})
        
        if response and response.posts:
            for post in response.posts:
                record = post.record
                author = post.author.display_name or post.author.handle
                text = record.text
                like_count = post.like_count if post.like_count is not None else 0
                repost_count = post.repost_count if post.repost_count is not None else 0
                reply_count = post.reply_count if post.reply_count is not None else 0
                created_at = record.created_at if hasattr(record, 'created_at') else None # Extract createdAt

                posts_data.append({
                    'hashtag': hashtag,
                    'author': author,
                    'text': text,
                    'likes': like_count,
                    'reposts': repost_count,
                    'replies': reply_count,
                    'uri': post.uri,
                    'created_at': created_at # Add createdAt to the data
                })
        else:
            print(f"No posts found for #{hashtag}.", file=sys.stderr)
    except Exception as e:
        print(f"Error searching Bluesky: {type(e).__name__}: {e}", file=sys.stderr)
    return posts_data

def main():
    parser = argparse.ArgumentParser(description="Scrape Bluesky posts by hashtag.")
    parser.add_argument("hashtag", help="The hashtag to search for (e.g., LearnGraph).")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of posts to retrieve.")
    args = parser.parse_args()

    client = get_bluesky_client()
    if client:
        posts = search_bluesky_hashtag(client, args.hashtag, args.limit)
        # Instead of printing formatted output, print the raw JSON data to stdout
        print(json.dumps(posts))

if __name__ == "__main__":
    main()
