import csv
import os
import sys
import datetime
import argparse
import webbrowser
import time
import subprocess # Added for running update_social_data.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader # Import Jinja2

def parse_csv_table(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
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

def generate_html(headers, rows, out_path):
    # Set up Jinja2 environment
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    template_dir = os.path.join(project_root, 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('report_template.html')

    # Render the template with data
    html = template.render(headers=headers, rows=rows)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML written to: {out_path}")

def generate_report(args):
    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        return

    if args.format == 'csv':
        headers, rows = parse_csv_table(args.input)
    elif args.format == 'md':
        headers, rows = parse_md_table(args.input)

    # Make any URLs clickable and use platform name as link text
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            # Skip the first column (Hashtag)
            if c == 0:
                continue
            
            # Check if the cell content is a URL
            if cell.startswith('http://') or cell.startswith('https://'):
                platform_name = headers[c].replace(' 🔗', '') # Remove the link emoji if present
                rows[r][c] = f'<a href="{cell}" target="_blank">{platform_name}</a>'

    # Create the output directory if it doesn't exist
    # Use the directory of the output file if specified, otherwise use the default output_dir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    output_dir = os.path.join(project_root, 'html')

    out_dir = os.path.dirname(args.output) if args.output else output_dir
    os.makedirs(out_dir, exist_ok=True)

    if args.output:
        out_file = args.output
    else:
        base = os.path.splitext(os.path.basename(args.input))[0]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        # Place the default output file in the html directory
        out_file = os.path.join(output_dir, f"{base}_{timestamp}.html")

    generate_html(headers, rows, out_file)

    if args.open_browser:
        webbrowser.open(f"file://{os.path.realpath(out_file)}")

class MyEventHandler(FileSystemEventHandler):
    def __init__(self, args):
        self.args = args

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.args.input:
            print(f"\nFile modified: {event.src_path}. Regenerating...")
            generate_report(self.args)

def main():
    # Get the absolute path of the script and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    
    # Define default input and output directories
    default_input = os.path.join(project_root, 'data', 'HashtagLinks.csv')
    output_dir = os.path.join(project_root, 'html')

    parser = argparse.ArgumentParser(description="Convert a CSV of hashtags to an HTML table.")
    parser.add_argument(
        "-i", "--input",
        default=default_input,
        help="Path to the input CSV file."
    )
    parser.add_argument(
        "-o", "--output",
        help=f"Path to the output HTML file. Defaults to a timestamped file in the '{output_dir}' directory."
    )
    parser.add_argument(
        "--no-open",
        dest="open_browser",
        action="store_false",
        help="Do not open the generated HTML file in a web browser."
    )
    parser.add_argument(
        "--format",
        choices=['csv', 'md'],
        default='csv',
        help="Input file format (csv or md)."
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
        help=argparse.SUPPRESS # Hidden argument for agent testing
    )
    parser.set_defaults(open_browser=True)
    args = parser.parse_args()

    if args.update_data:
        print("Updating social data...")
        update_script_path = os.path.join(script_dir, 'update_social_data.py')
        subprocess.run([sys.executable, update_script_path])

    if args.watch:
        print(f"Watching {args.input} for changes... Press Ctrl+C to stop.")
        event_handler = MyEventHandler(args)
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(args.input), recursive=False)
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
        generate_report(args)

if __name__ == "__main__":
    main()
    # If the script is running in an interactive terminal, wait for user input.
    if sys.stdout.isatty():
        input("Press Enter to exit...")