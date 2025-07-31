import re
import csv
import os
import sys
import datetime
import argparse
import time
import subprocess # Added for running update_social_data.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader # Import Jinja2
import json
from collections import defaultdict
import numpy as np

def parse_csv_table(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = []
        for row in reader:
            if len(row) > 2:
                hashtag = row[0].lstrip('#')
                row[2] = f"https://old.reddit.com/r/{hashtag}"
            rows.append(row)
    return headers, rows

def parse_md_table(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    headers = [cell.strip() for cell in lines[0].split('|') if cell.strip()]
    rows = []
    for line in lines[2:]:  # Skip header and separator
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        rows.append(cells)
    return headers, rows

def read_analytics_data(csv_path):
    daily_posts = defaultdict(list)
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['metric'] == 'daily_posts':
                    hashtag = row['hashtag']
                    value = int(row['value'])
                    daily_posts[hashtag].append(value)
        
        # Calculate hotness based on quantiles
        all_max_posts = [max(posts) for posts in daily_posts.values() if posts]
        if not all_max_posts:
            return {}, 0, {}

        quantiles = np.percentile(all_max_posts, [25, 50, 75])
        hotness_levels = {}
        for hashtag, posts in daily_posts.items():
            max_posts = max(posts) if posts else 0
            if max_posts <= quantiles[0]:
                hotness_levels[hashtag] = 0  # Low
            elif max_posts <= quantiles[1]:
                hotness_levels[hashtag] = 1  # Medium
            elif max_posts <= quantiles[2]:
                hotness_levels[hashtag] = 2  # High
            else:
                hotness_levels[hashtag] = 3  # Very High

        print(f"[DEBUG] Loaded Bluesky analytics data for {len(daily_posts)} hashtags.")
        return daily_posts, max(all_max_posts), hotness_levels

    except FileNotFoundError:
        print(f"[WARNING] Bluesky Analytics CSV file not found: {csv_path}. Proceeding without Bluesky analytics.")
        return {}, 0, {}
    except Exception as e:
        print(f"[ERROR] Error reading Bluesky analytics CSV: {e}")
        return {}, 0, {}

def read_reddit_analytics_data(csv_path):
    reddit_analytics_data = {}
    max_subscribers = 0
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                subreddit = row.get('subreddit')
                subscribers_str = row.get('subscribers')
                if subreddit and subscribers_str and subscribers_str.isdigit():
                    subscribers = int(subscribers_str)
                    reddit_analytics_data[subreddit] = subscribers
                    if subscribers > max_subscribers:
                        max_subscribers = subscribers
        print(f"[DEBUG] Loaded Reddit analytics data for {len(reddit_analytics_data)} subreddits. Max subscribers: {max_subscribers}")
    except FileNotFoundError:
        print(f"[WARNING] Reddit Analytics CSV file not found: {csv_path}. Proceeding without Reddit analytics.")
    except Exception as e:
        print(f"[ERROR] Error reading Reddit analytics CSV: {e}")
    return reddit_analytics_data, max_subscribers

def read_youtube_analytics_data(csv_path):
    youtube_analytics_data = {}
    hotness_levels = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_views = [int(row['total_views']) for row in reader if row.get('total_views') and row['total_views'].isdigit()]
            f.seek(0) # Reset file pointer
            next(reader) # Skip header
            if not all_views:
                return {}, {}

            quantiles = np.percentile(all_views, [25, 50, 75])
            for row in reader:
                hashtag = row.get('hashtag')
                if hashtag:
                    youtube_analytics_data[hashtag] = row
                    views_str = row.get('total_views', '0')
                    views = int(views_str) if views_str.isdigit() else 0
                    if views <= quantiles[0]:
                        hotness_levels[hashtag] = 0  # Low
                    elif views <= quantiles[1]:
                        hotness_levels[hashtag] = 1  # Medium
                    elif views <= quantiles[2]:
                        hotness_levels[hashtag] = 2  # High
                    else:
                        hotness_levels[hashtag] = 3  # Very High

        print(f"[DEBUG] Loaded YouTube analytics data for {len(youtube_analytics_data)} hashtags.")
    except FileNotFoundError:
        print(f"[WARNING] YouTube Analytics CSV file not found: {csv_path}. Proceeding without YouTube analytics.")
    except Exception as e:
        print(f"[ERROR] Error reading YouTube analytics CSV: {e}")
    return youtube_analytics_data, hotness_levels

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_html(headers, rows, out_path, analytics_data, max_daily_posts, hotness_levels, reddit_analytics_data, max_subscribers, youtube_analytics_data, youtube_hotness_levels, config):
    # Set up Jinja2 environment
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    template_dir = os.path.join(project_root, 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('report_template.html')

    # Render the template with data
    html = template.render(
        headers=headers,
        rows=rows,
        analytics_data=analytics_data,
        max_daily_posts=max_daily_posts,
        hotness_levels=hotness_levels,
        reddit_analytics_data=reddit_analytics_data,
        max_subscribers=max_subscribers,
        youtube_analytics_data=youtube_analytics_data,
        youtube_hotness_levels=youtube_hotness_levels,
        reddit_status_colors=config['reddit_status_colors'],
        subreddit_status=config['subreddit_status']
    )

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML written to: {out_path}")

def generate_report(args, config):
    hashtags = config.get('hashtags', [])
    platform_url_templates = config.get('platform_url_templates', {})
    headers = ['Hashtag'] + list(platform_url_templates.keys())
    rows = []
    for hashtag in hashtags:
        row = [f'#{hashtag}']
        for platform in platform_url_templates:
            url = platform_url_templates[platform].format(hashtag)
            row.append(url)
        rows.append(row)

    # Read analytics data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    bluesky_analytics_csv_path = os.path.join(project_root, 'data', 'BlueskyAnalytics.csv')
    analytics_data, max_daily_posts, hotness_levels = read_analytics_data(bluesky_analytics_csv_path)

    reddit_analytics_csv_path = os.path.join(project_root, 'data', 'RedditAnalytics.csv')
    reddit_analytics_data, max_subscribers = read_reddit_analytics_data(reddit_analytics_csv_path)

    youtube_analytics_csv_path = os.path.join(project_root, 'data', 'YouTubeAnalytics.csv')
    youtube_analytics_data, youtube_hotness_levels = read_youtube_analytics_data(youtube_analytics_csv_path)

    print(f"[DEBUG] Bluesky Analytics Data passed to template: {analytics_data}")
    print(f"[DEBUG] Max Daily Posts passed to template: {max_daily_posts}")
    print(f"[DEBUG] Reddit Analytics Data passed to template: {max_subscribers}")
    print(f"[DEBUG] YouTube Analytics Data passed to template: {youtube_analytics_data}")

    # Create the output directory if it doesn't exist
    output_dir = os.path.join(project_root, 'html')
    out_dir = os.path.dirname(args.output) if args.output else output_dir
    os.makedirs(out_dir, exist_ok=True)

    if args.output:
        out_file = args.output
    else:
        base = 'HashtagReport'
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        out_file = os.path.join(output_dir, f"{base}_{timestamp}.html")

    generate_html(headers, rows, out_file, analytics_data, max_daily_posts, hotness_levels, reddit_analytics_data, max_subscribers, youtube_analytics_data, youtube_hotness_levels, config)


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, args, config):
        self.args = args
        self.config = config

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.args.input:
            print(f"\nFile modified: {event.src_path}. Regenerating...")
            generate_report(self.args, self.config)

def main():
    # Get the absolute path of the script and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    
    output_dir = os.path.join(project_root, 'html')
    config_path = os.path.join(project_root, 'config.json')

    parser = argparse.ArgumentParser(description="Convert a CSV of hashtags to an HTML table.")
    parser.add_argument(
        "-o", "--output",
        help=f"Path to the output HTML file. Defaults to a timestamped file in the '{output_dir}' directory."
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the input file for changes and regenerate the HTML automatically."
    )
    parser.add_argument(
        "--update-data",
        action="store_true",
        help="Run the social data update script before generating the HTML report."
    )
    parser.add_argument(
        "--agent-timeout",
        type=int,
        default=0,
        help=argparse.SUPPRESS
    )
    args = parser.parse_args()

    config = load_config(config_path)

    if args.update_data:
        print("Updating social data...")
        update_script_path = os.path.join(script_dir, 'update_social_data.py')
        subprocess.run([sys.executable, update_script_path])

    if args.watch:
        print(f"Watching {config_path} for changes... Press Ctrl+C to stop.")
        event_handler = MyEventHandler(args, config)
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(config_path), recursive=False)
        observer.start()
        try:
            start_time = time.time()
            while True:
                if args.agent_timeout and (time.time() - start_time > args.agent_timeout):
                    print(f"\nAgent timeout reached ({args.agent_timeout} seconds). Stopping watch mode.")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
    else:
        generate_report(args, config)

if __name__ == "__main__":
    main()
    if sys.stdout.isatty():
        input("Press Enter to exit...")