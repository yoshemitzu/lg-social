import subprocess
import sys
import os
import webbrowser
import glob
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate and open the LearnGraph report.")
    parser.add_argument(
        "--no-update",
        action="store_true",
        help="Skip the data update process before generating the report."
    )
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.abspath(__file__))
    make_html_script_path = os.path.join(project_root, 'scripts', 'make-html.py')
    html_dir = os.path.join(project_root, 'html')

    print("Generating HTML report...")
    command = [sys.executable, make_html_script_path]
    if not args.no_update:
        print("Updating data...")
        command.append('--update-data')
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        
        # Find the most recent HTML file
        list_of_files = glob.glob(os.path.join(html_dir, '*.html'))
        if not list_of_files:
            print("No HTML files found in the html directory.")
            return

        latest_file = max(list_of_files, key=os.path.getctime)
        print(f"Report generated: {latest_file}")
        
        # Open the file in the browser
        webbrowser.open(f"file://{os.path.realpath(latest_file)}")
        print("Report opened in browser.")

    except subprocess.CalledProcessError as e:
        print("Error generating report:")
        print(e.stdout)
        print(e.stderr)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
