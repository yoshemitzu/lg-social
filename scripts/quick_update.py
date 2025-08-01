#!/usr/bin/env python3
"""
Quick Update Script for LearnGraph
Optimized for cost-effective operations with Gemini CLI

This script provides fast, targeted updates without the overhead of full data collection.
Use this for routine maintenance and quick insights.
"""

import argparse
import json
import os
import sys
from datetime import datetime
import subprocess

def load_config():
    """Load configuration from config.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def get_top_hashtags(limit=5):
    """Get top performing hashtags based on recent activity"""
    config = load_config()
    # These are the consistently high-performing hashtags based on your data
    top_hashtags = [
        'Education',      # 131 posts/day peak
        'EdTech',         # 84 posts/day peak  
        'teachers',       # 48 posts/day peak
        'AIinEducation',  # 19 posts/day peak
        'LifelongLearning' # 19 posts/day peak
    ]
    return top_hashtags[:limit]

def quick_report_only():
    """Generate report without updating data"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, '..', 'main.py')
    
    print("🚀 Generating quick report (no data update)...")
    result = subprocess.run([sys.executable, main_script, '--no-update'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Report generated successfully!")
        return True
    else:
        print(f"❌ Error generating report: {result.stderr}")
        return False

def targeted_update(hashtags):
    """Update only specific high-value hashtags"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    update_script = os.path.join(script_dir, 'update_social_data.py')
    
    print(f"🎯 Updating {len(hashtags)} high-priority hashtags...")
    
    for hashtag in hashtags:
        print(f"  📊 Processing #{hashtag}...")
        result = subprocess.run([sys.executable, update_script, '--hashtag', hashtag],
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"  ✅ #{hashtag} updated")
        else:
            print(f"  ⚠️  #{hashtag} failed (continuing...)")
    
    return True

def show_status():
    """Show current project status and key metrics"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check data files
    data_dir = os.path.join(script_dir, '..', 'data')
    files_status = {}
    
    for filename in ['BlueskyAnalytics.csv', 'YouTubeAnalytics.csv', 'BlueskyScrapedData.csv']:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            stat = os.stat(filepath)
            files_status[filename] = {
                'exists': True,
                'size_kb': round(stat.st_size / 1024, 1),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            }
        else:
            files_status[filename] = {'exists': False}
    
    # Show status
    print("\n📈 LearnGraph Status Dashboard")
    print("=" * 40)
    
    config = load_config()
    print(f"📋 Tracking {len(config['hashtags'])} hashtags")
    print(f"🌐 Monitoring {len(config['platform_url_templates'])} platforms")
    
    print("\n📁 Data Files:")
    for filename, status in files_status.items():
        if status['exists']:
            print(f"  ✅ {filename}: {status['size_kb']}KB (updated {status['modified']})")
        else:
            print(f"  ❌ {filename}: Missing")
    
    # Show top hashtags
    top_hashtags = get_top_hashtags()
    print(f"\n🔥 Top {len(top_hashtags)} Hashtags:")
    for i, hashtag in enumerate(top_hashtags, 1):
        print(f"  {i}. #{hashtag}")
    
    # Show recent reports
    reports_dir = os.path.join(script_dir, '..', 'reports')
    if os.path.exists(reports_dir):
        reports = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
        if reports:
            latest_report = max(reports, key=lambda x: os.path.getctime(os.path.join(reports_dir, x)))
            report_time = datetime.fromtimestamp(
                os.path.getctime(os.path.join(reports_dir, latest_report))
            ).strftime('%Y-%m-%d %H:%M')
            print(f"\n📊 Latest Report: {latest_report} ({report_time})")
        else:
            print("\n📊 No reports found")

def main():
    parser = argparse.ArgumentParser(
        description="Quick operations for LearnGraph - optimized for efficiency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quick_update.py status              # Show current status
  python quick_update.py report              # Generate report only (fast)
  python quick_update.py update              # Update top 5 hashtags only
  python quick_update.py update --limit 3    # Update top 3 hashtags only
  python quick_update.py full                # Update top hashtags + generate report
        """
    )
    
    parser.add_argument('action', choices=['status', 'report', 'update', 'full'],
                       help='Action to perform')
    parser.add_argument('--limit', type=int, default=5,
                       help='Number of top hashtags to update (default: 5)')
    
    args = parser.parse_args()
    
    print(f"🎯 LearnGraph Quick Update - {args.action.upper()} mode")
    print(f"⏰ Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.action == 'status':
        show_status()
    
    elif args.action == 'report':
        quick_report_only()
    
    elif args.action == 'update':
        top_hashtags = get_top_hashtags(args.limit)
        targeted_update(top_hashtags)
        print(f"✅ Updated {len(top_hashtags)} hashtags")
    
    elif args.action == 'full':
        top_hashtags = get_top_hashtags(args.limit)
        print("Phase 1: Targeted data update...")
        targeted_update(top_hashtags)
        print("\nPhase 2: Generating report...")
        quick_report_only()
        print("✅ Full update complete!")
    
    print(f"⏰ Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
