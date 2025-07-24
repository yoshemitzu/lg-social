import csv
import os
import subprocess
import sys
import json
from collections import defaultdict
from datetime import datetime

def read_hashtags_from_csv(csv_path):
    print(f"[DEBUG] Reading hashtags from: {csv_path}")
    hashtags = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                if row:
                    hashtags.append(row[0])  # Assuming hashtag is in the first column
        print(f"[DEBUG] Found {len(hashtags)} hashtags.")
    except FileNotFoundError:
        print(f"[ERROR] Hashtag CSV file not found: {csv_path}")
    except Exception as e:
        print(f"[ERROR] Error reading hashtag CSV: {e}")
    return hashtags

def run_bluesky_scraper(hashtag, limit=10):
    print(f"[DEBUG] Running Bluesky scraper for hashtag: #{hashtag} with limit: {limit}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scraper_path = os.path.join(script_dir, 'bluesky_scraper.py')
    
    command = [sys.executable, scraper_path, hashtag, '--limit', str(limit)]
    print(f"[DEBUG] Scraper command: {' '.join(command)}")
    
    # Set PYTHONIOENCODING to utf-8 for the subprocess
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    # Capture stdout and stderr
    try:
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True, env=env) # Added env=env
        
        # Parse the JSON output from the scraper
        if process.stdout:
            scraped_data = json.loads(process.stdout)
            print(f"[DEBUG] Scraper stdout for #{hashtag}:\n{process.stdout}") # Still print for debug
        else:
            scraped_data = []
            print(f"[DEBUG] Scraper stdout for #{hashtag} was empty.")

        if process.stderr:
            print(f"[DEBUG] Scraper stderr for #{hashtag}:\n{process.stderr}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Scraper process failed for #{hashtag} (Exit Code: {e.returncode}):\n{e.stderr}")
        return []
    except FileNotFoundError:
        print(f"[ERROR] bluesky_scraper.py not found at: {scraper_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decoding error for #{hashtag}: {e}\nRaw stdout: {process.stdout}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error running scraper for #{hashtag}: {e}")
        return []
    
    print(f"[DEBUG] Scraped {len(scraped_data)} posts for #{hashtag}.")
    return scraped_data

def write_scraped_data_to_csv(data, output_csv_path, write_header=False):
    print(f"[DEBUG] Writing scraped data to: {output_csv_path}")
    fieldnames = ['hashtag', 'author', 'text', 'likes', 'reposts', 'replies', 'uri', 'created_at']

    try:
        with open(output_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()  # Write header only if explicitly requested
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

    # Daily Posts
    for hashtag, dates in daily_posts.items():
        for date, count in dates.items():
            analytics_data.append({
                'metric': 'daily_posts',
                'hashtag': hashtag,
                'date': date,
                'value': count
            })
    
    # Major Posters (by activity)
    for hashtag, authors in author_activity.items():
        sorted_authors = sorted(authors.items(), key=lambda item: item[1], reverse=True)
        for author, count in sorted_authors[:5]: # Top 5 by activity
            analytics_data.append({
                'metric': 'top_poster_activity',
                'hashtag': hashtag,
                'author': author,
                'value': count
            })

    # Major Posters (by engagement)
    for hashtag, authors in author_engagement.items():
        sorted_authors = sorted(authors.items(), key=lambda item: item[1], reverse=True)
        for author, engagement in sorted_authors[:5]: # Top 5 by engagement
            analytics_data.append({
                'metric': 'top_poster_engagement',
                'hashtag': hashtag,
                'author': author,
                'value': engagement
            })
    print(f"[DEBUG] Generated {len(analytics_data)} analytics records.")
    return analytics_data

def write_analytics_to_csv(data, output_csv_path):
    print(f"[DEBUG] Writing analytics data to: {output_csv_path}")
    fieldnames = ['metric', 'hashtag', 'date', 'author', 'value']
    
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()  # Always write header for analytics, as it's a new run
            writer.writerows(data)
        print(f"[DEBUG] Analytics data written to {output_csv_path}")
    except Exception as e:
        print(f"[ERROR] Error writing analytics CSV: {e}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    
    hashtags_csv_path = os.path.join(project_root, 'data', 'HashtagLinks.csv')
    output_scraped_csv_path = os.path.join(project_root, 'data', 'BlueskyScrapedData.csv')
    output_analytics_csv_path = os.path.join(project_root, 'data', 'BlueskyAnalytics.csv')

    print("[DEBUG] Starting update_social_data.py main function.")
    hashtags = read_hashtags_from_csv(hashtags_csv_path)
    
    # Clear previous scraped data before starting a new run
    if os.path.exists(output_scraped_csv_path):
        os.remove(output_scraped_csv_path)

    # Write header for scraped data only once at the beginning
    write_scraped_data_to_csv([], output_scraped_csv_path, write_header=True)

    all_scraped_data_for_analytics = [] # Collect all data for final analytics

    if not hashtags:
        print("[DEBUG] No hashtags found or error reading CSV. Exiting.")
        return

    for hashtag in hashtags:
        # Remove the # from the hashtag for the scraper argument
        clean_hashtag = hashtag.lstrip('#')
        scraped_posts = run_bluesky_scraper(clean_hashtag, limit=5) # Limiting to 5 for testing
        
        if scraped_posts:
            write_scraped_data_to_csv(scraped_posts, output_scraped_csv_path) # Write incrementally
            all_scraped_data_for_analytics.extend(scraped_posts)
        else:
            print(f"[DEBUG] No posts scraped for #{hashtag}. Skipping incremental write.")
    
    if all_scraped_data_for_analytics:
        print("[DEBUG] Processing all scraped data for final analytics...")
        analytics_data = analyze_bluesky_data(all_scraped_data_for_analytics)
        write_analytics_to_csv(analytics_data, output_analytics_csv_path)
    else:
        print("No data scraped across all hashtags. Check Bluesky credentials and network connection.")

if __name__ == "__main__":
    main()