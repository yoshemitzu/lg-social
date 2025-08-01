import re
import csv
import os
import subprocess
import sys
import json
import argparse
from collections import defaultdict
from datetime import datetime

def read_hashtags_from_config(config_path):
    print(f"[DEBUG] Reading hashtags from: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        hashtags = config.get('hashtags', [])
        platform_url_templates = config.get('platform_url_templates', {})
        hashtag_data = []
        for hashtag in hashtags:
            platforms = {platform: template.format(hashtag) for platform, template in platform_url_templates.items()}
            hashtag_data.append({'hashtag': hashtag, 'platforms': platforms})
        print(f"[DEBUG] Found {len(hashtag_data)} hashtags.")
        return hashtag_data
    except FileNotFoundError:
        print(f"[ERROR] Config file not found: {config_path}")
    except Exception as e:
        print(f"[ERROR] Error reading config file: {e}")
    return []

def get_existing_post_uris(csv_path):
    """Reads a CSV file and returns a set of post URIs."""
    if not os.path.exists(csv_path):
        return set()
    
    uris = set()
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'uri' in row:
                    uris.add(row['uri'])
    except Exception as e:
        print(f"[ERROR] Could not read existing scraped data from {csv_path}: {e}")
    print(f"[DEBUG] Found {len(uris)} existing post URIs.")
    return uris

def get_existing_youtube_hashtags(csv_path):
    """Reads a CSV file and returns a set of hashtags."""
    if not os.path.exists(csv_path):
        return set()
    
    hashtags = set()
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'hashtag' in row:
                    hashtags.add(row['hashtag'])
    except Exception as e:
        print(f"[ERROR] Could not read existing YouTube data from {csv_path}: {e}")
    print(f"[DEBUG] Found {len(hashtags)} existing YouTube hashtags.")
    return hashtags

def read_all_scraped_data(csv_path):
    """Reads all data from the scraped data CSV."""
    data = []
    if not os.path.exists(csv_path):
        return data
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row['likes'] = int(row.get('likes', 0))
                row['reposts'] = int(row.get('reposts', 0))
                row['replies'] = int(row.get('replies', 0))
                data.append(row)
    except Exception as e:
        print(f"[ERROR] Could not read all scraped data from {csv_path}: {e}")
    print(f"[DEBUG] Read {len(data)} total posts for analysis.")
    return data

def run_scraper(scraper_path, args, timeout=60):
    """Runs a scraper script as a subprocess."""
    command = [sys.executable, scraper_path] + args
    print(f"[DEBUG] Scraper command: {' '.join(command)}", file=sys.stderr)
    
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        process = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            check=True, 
            env=env,
            timeout=timeout
        )
        
        if process.stdout:
            if process.stderr:
                print(f"[DEBUG] Scraper stderr for {scraper_path}:\n{process.stderr}", file=sys.stderr)
            return json.loads(process.stdout)
        else:
            print(f"[DEBUG] Scraper stdout for {scraper_path} was empty.")
            if process.stderr:
                print(f"[DEBUG] Scraper stderr for {scraper_path}:\n{process.stderr}", file=sys.stderr)
            return None

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Scraper process failed for {scraper_path} (Exit Code: {e.returncode}):\n{e.stderr}")
    except FileNotFoundError:
        print(f"[ERROR] {scraper_path} not found.")
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decoding error for {scraper_path}: {e}\nRaw stdout: {process.stdout}")
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Scraper process timed out for {scraper_path}.")
    except Exception as e:
        print(f"[ERROR] Unexpected error running scraper {scraper_path}: {e}")
    
    return None

def write_reddit_data_to_csv(data, output_csv_path):
    print(f"[DEBUG] Writing Reddit data to: {output_csv_path}")
    fieldnames = ['subreddit', 'subscribers', 'active_user_count', 'posts_count', 'avg_score', 'avg_comments']

    file_exists = os.path.exists(output_csv_path)

    try:
        with open(output_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists or os.stat(output_csv_path).st_size == 0:
                writer.writeheader()
            writer.writerow(data)
        print(f"[DEBUG] Reddit data written to {output_csv_path}")
    except Exception as e:
        print(f"[ERROR] Error writing Reddit data CSV: {e}")

def write_youtube_data_to_csv(data, output_csv_path):
    print(f"[DEBUG] Writing YouTube data to: {output_csv_path}")
    fieldnames = ['hashtag', 'total_views', 'total_likes', 'total_comments', 'top_video_url']

    # Read existing data
    existing_data = []
    if os.path.exists(output_csv_path):
        with open(output_csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_data.append(row)

    # Update or add new data
    updated = False
    for i, row in enumerate(existing_data):
        if row['hashtag'] == data['hashtag']:
            existing_data[i] = data
            updated = True
            break
    if not updated:
        existing_data.append(data)

    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_data)
        print(f"[DEBUG] YouTube data written to {output_csv_path}")
    except Exception as e:
        print(f"[ERROR] Error writing YouTube data CSV: {e}")

def write_scraped_data_to_csv(data, output_csv_path, write_header=False):
    print(f"[DEBUG] Appending {len(data)} new posts to: {output_csv_path}")
    fieldnames = ['hashtag', 'author', 'text', 'likes', 'reposts', 'replies', 'uri', 'created_at']

    try:
        with open(output_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(data)
        print(f"[DEBUG] Scraped data written to {output_csv_path}")
    except Exception as e:
        print(f"[ERROR] Error writing scraped data CSV: {e}")

def analyze_bluesky_data(scraped_data):
    print("[DEBUG] Analyzing Bluesky data...")
    daily_posts = defaultdict(lambda: defaultdict(int))
    author_activity = defaultdict(lambda: defaultdict(int))
    author_engagement = defaultdict(lambda: defaultdict(int))

    for post in scraped_data:
        hashtag = post['hashtag']
        author = post['author']
        created_at_str = post.get('created_at')
        likes = post.get('likes', 0)
        reposts = post.get('reposts', 0)
        replies = post.get('replies', 0)

        if created_at_str:
            try:
                post_date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')).date()
                daily_posts[hashtag][str(post_date)] += 1
            except ValueError:
                print(f"[WARNING] Could not parse date {created_at_str} for post {post.get('uri')}")

        author_activity[hashtag][author] += 1
        author_engagement[hashtag][author] += (likes + reposts + replies)

    analytics_data = []

    for hashtag, dates in daily_posts.items():
        for date, count in dates.items():
            analytics_data.append({'metric': 'daily_posts', 'hashtag': hashtag, 'date': date, 'author': None, 'value': count})
    
    for hashtag, authors in author_activity.items():
        sorted_authors = sorted(authors.items(), key=lambda item: item[1], reverse=True)
        for author, count in sorted_authors[:5]:
            analytics_data.append({'metric': 'top_poster_activity', 'hashtag': hashtag, 'author': author, 'date': None, 'value': count})

    for hashtag, authors in author_engagement.items():
        sorted_authors = sorted(authors.items(), key=lambda item: item[1], reverse=True)
        for author, engagement in sorted_authors[:5]:
            analytics_data.append({'metric': 'top_poster_engagement', 'hashtag': hashtag, 'author': author, 'date': None, 'value': engagement})
            
    print(f"[DEBUG] Generated {len(analytics_data)} analytics records.")
    return analytics_data

def write_analytics_to_csv(data, output_csv_path):
    print(f"[DEBUG] Writing analytics data to: {output_csv_path}")
    fieldnames = ['metric', 'hashtag', 'date', 'author', 'value']
    
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"[DEBUG] Analytics data written to {output_csv_path}")
    except Exception as e:
        print(f"[ERROR] Error writing analytics CSV: {e}")

def process_single_hashtag(entry, script_dir, project_root, existing_uris, existing_youtube_hashtags, output_scraped_csv_path, output_reddit_analytics_csv_path, output_youtube_analytics_csv_path):
    hashtag = entry['hashtag']
    platforms = entry['platforms']
    new_posts_found_for_hashtag = False
    all_new_posts_for_hashtag = []

    if 'Bluesky' in platforms and platforms['Bluesky']:
        print(f"[DEBUG] Processing Bluesky for #{hashtag}")
        bluesky_scraper_path = os.path.join(script_dir, 'bluesky_scraper.py')
        scraped_posts = run_scraper(bluesky_scraper_path, [hashtag, '--limit', '100'])
        print(f"[DEBUG] Bluesky scraper returned {len(scraped_posts) if scraped_posts else 0} posts for #{hashtag}")
        if scraped_posts:
            new_posts = [post for post in scraped_posts if post['uri'] not in existing_uris]

            if new_posts:
                new_posts_found_for_hashtag = True
                print(f"[INFO] Found {len(new_posts)} new posts for #{hashtag}.")
                all_new_posts_for_hashtag.extend(new_posts)
                for post in new_posts:
                    existing_uris.add(post['uri'])
            else:
                print(f"[DEBUG] No new Bluesky posts found for #{hashtag}.")
    
    if 'Reddit' in platforms and platforms['Reddit']:
        reddit_url = platforms['Reddit']
        match = re.search(r'reddit\\.com/r/([^/]+)', reddit_url)
        if match:
            subreddit_name = match.group(1)
            reddit_scraper_path = os.path.join(script_dir, 'reddit_scraper.py')
            reddit_data = run_scraper(reddit_scraper_path, [subreddit_name])
            
            if reddit_data:
                processed_reddit_data = {
                    'subreddit': subreddit_name,
                    'subscribers': reddit_data.get('subscribers', 0),
                    'active_user_count': reddit_data.get('active_user_count', 0),
                    'posts_count': len(reddit_data.get('posts', [])),
                    'avg_score': sum(p['score'] for p in reddit_data.get('posts', [])) / len(reddit_data['posts']) if reddit_data.get('posts') else 0,
                    'avg_comments': sum(p['num_comments'] for p in reddit_data.get('posts', [])) / len(reddit_data['posts']) if reddit_data.get('posts') else 0
                }
                write_reddit_data_to_csv(processed_reddit_data, output_reddit_analytics_csv_path)

    if 'YouTube' in platforms and platforms['YouTube']:
        print(f"[DEBUG] Processing YouTube for #{hashtag}")
        youtube_scraper_path = os.path.join(script_dir, 'youtube_scraper.py')
        videos = run_scraper(youtube_scraper_path, [hashtag, '--limit', '5'])
        
        
        youtube_analytics = {
            'hashtag': hashtag,
            'total_views': sum(v.get('view_count') or 0 for v in videos),
            'total_likes': sum(v.get('like_count') or 0 for v in videos),
            'total_comments': sum(v.get('comment_count') or 0 for v in videos),
            'top_video_url': videos[0].get('url') if videos else ""
        }
        print(f"[DEBUG] YouTube analytics for #{hashtag} before writing: {youtube_analytics}".encode('utf-8', 'ignore').decode('utf-8'))
        
        write_youtube_data_to_csv(youtube_analytics, output_youtube_analytics_csv_path)
    return new_posts_found_for_hashtag, all_new_posts_for_hashtag

def main():
    parser = argparse.ArgumentParser(description="Update social media data for hashtags.")
    parser.add_argument("--hashtag", help="Process only a specific hashtag.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    
    config_path = os.path.join(project_root, 'config.json')
    output_scraped_csv_path = os.path.join(project_root, 'data', 'BlueskyScrapedData.csv')
    output_analytics_csv_path = os.path.join(project_root, 'data', 'BlueskyAnalytics.csv')
    output_reddit_analytics_csv_path = os.path.join(project_root, 'data', 'RedditAnalytics.csv')
    output_youtube_analytics_csv_path = os.path.join(project_root, 'data', 'YouTubeAnalytics.csv')

    print("[DEBUG] Starting incremental update_social_data.py.")
    hashtag_data = read_hashtags_from_config(config_path)
    
    existing_uris = get_existing_post_uris(output_scraped_csv_path)
    existing_youtube_hashtags = get_existing_youtube_hashtags(output_youtube_analytics_csv_path)
    
    if os.path.exists(output_reddit_analytics_csv_path):
        os.remove(output_reddit_analytics_csv_path)

    file_exists = os.path.exists(output_scraped_csv_path)
    if not file_exists:
        write_scraped_data_to_csv([], output_scraped_csv_path, write_header=True)

    new_posts_found = False
    all_new_posts = []

    if not hashtag_data:
        print("[DEBUG] No hashtags found or error reading config. Exiting.")
        return

    print(f"[DEBUG] Existing YouTube hashtags before processing: {existing_youtube_hashtags}")
    if args.hashtag:
        # Process only the specified hashtag
        cleaned_hashtag_arg = args.hashtag.strip('"')
        filtered_hashtag_data = [entry for entry in hashtag_data if entry['hashtag'].lower() == cleaned_hashtag_arg.lower()]
        if not filtered_hashtag_data:
            print(f"[ERROR] Hashtag '{args.hashtag}' not found in config.json. Exiting.")
            return
        for entry in filtered_hashtag_data:
            found, new_posts = process_single_hashtag(entry, script_dir, project_root, existing_uris, existing_youtube_hashtags, output_scraped_csv_path, output_reddit_analytics_csv_path, output_youtube_analytics_csv_path)
            if found:
                new_posts_found = True
                all_new_posts.extend(new_posts)
    else:
        # Process all hashtags
        for entry in hashtag_data:
            found, new_posts = process_single_hashtag(entry, script_dir, project_root, existing_uris, existing_youtube_hashtags, output_scraped_csv_path, output_reddit_analytics_csv_path, output_youtube_analytics_csv_path)
            if found:
                new_posts_found = True
                all_new_posts.extend(new_posts)

    if all_new_posts:
        write_scraped_data_to_csv(all_new_posts, output_scraped_csv_path)

    if new_posts_found:
        print("[DEBUG] New posts were found. Re-analyzing all Bluesky data...")
        all_scraped_data = read_all_scraped_data(output_scraped_csv_path)
        analytics_data = analyze_bluesky_data(all_scraped_data)
        write_analytics_to_csv(analytics_data, output_analytics_csv_path)
    else:
        print("[DEBUG] No new posts found. Analytics file is up-to-date.")

if __name__ == "__main__":
    main()