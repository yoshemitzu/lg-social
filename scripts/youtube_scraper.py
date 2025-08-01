import json
import subprocess
import sys
import argparse

def search_youtube(hashtag, limit=5):
    """Searches YouTube for a given hashtag and returns video metadata."""
    search_query = f"ytsearch{limit}:{hashtag}"
    command = [
        'yt-dlp',
        '--dump-json',
        '--no-download',
        '--ignore-errors',
        search_query
    ]
    

    try:
        process = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            check=True
        )
        
        videos = []
        for line in process.stdout.strip().split('\n'):
            video_data = json.loads(line)
            videos.append({
                'hashtag': hashtag,
                'title': video_data.get('title'),
                'url': video_data.get('webpage_url'),
                'channel': video_data.get('channel'),
                'view_count': video_data.get('view_count'),
                'like_count': video_data.get('like_count'),
                'comment_count': video_data.get('comment_count')
            })
        return videos

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] yt-dlp failed for hashtag '{hashtag}': {e.stderr}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while searching YouTube for '{hashtag}': {e}", file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser(description="Search YouTube for videos with a specific hashtag.")
    parser.add_argument("hashtag", help="The hashtag to search for.")
    parser.add_argument("--limit", type=int, default=5, help="The maximum number of videos to return.")
    args = parser.parse_args()

    videos = search_youtube(args.hashtag, args.limit)
    print(json.dumps(videos))

if __name__ == "__main__":
    main()
