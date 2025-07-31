import json
import csv
import os

def generate_hashtag_links_csv():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    config_path = os.path.join(project_root, 'config.json')
    output_csv_path = os.path.join(project_root, 'data', 'HashtagLinks.csv')

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    hashtags = config.get('hashtags', [])
    platform_templates = config.get('platform_url_templates', {})

    header = ['Hashtag'] + list(platform_templates.keys())

    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for hashtag in hashtags:
            row = [f'#{hashtag}']
            for platform in platform_templates:
                url = platform_templates[platform].format(hashtag)
                row.append(url)
            writer.writerow(row)

    print(f"Successfully generated {output_csv_path}")

if __name__ == "__main__":
    generate_hashtag_links_csv()
