import sys
import codecs

if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid # For generating unique task IDs

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
GREMLIN_INSTRUCTIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gremlin_instructions.json')

def add_gremlin_task(task_id, command):
    try:
        instructions = []
        if os.path.exists(GREMLIN_INSTRUCTIONS_FILE):
            with open(GREMLIN_INSTRUCTIONS_FILE, 'r', encoding='utf-8') as f:
                try:
                    instructions = json.load(f)
                except json.JSONDecodeError:
                    instructions = [] # File is empty or corrupted, start fresh
        
        instructions.append({'task_id': task_id, 'command': command})
        
        with open(GREMLIN_INSTRUCTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(instructions, f, indent=2, ensure_ascii=False)
        print(f"[API_SERVER] Added task {task_id} to Gremlin instructions.")
    except Exception as e:
        print(f"[API_SERVER] Error adding task to Gremlin instructions: {e}")

@app.route('/add_hashtag', methods=['POST'])
def add_hashtag():
    data = request.get_json()
    new_hashtag = data.get('hashtag')

    if not new_hashtag:
        return jsonify({'status': 'error', 'message': 'No hashtag provided'}), 400

    try:
        with open(CONFIG_FILE, 'r+', encoding='utf-8') as f:
            config = json.load(f)
            hashtags = config.get('hashtags', [])
            
            # Add only if not already present (case-insensitive)
            if new_hashtag.lower() not in [h.lower() for h in hashtags]:
                hashtags.append(new_hashtag)
                config['hashtags'] = hashtags
                f.seek(0)  # Rewind to the beginning of the file
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.truncate() # Truncate any remaining old content

                # Add a task for Gremlin to update social data for the new hashtag
                task_id = str(uuid.uuid4())
                update_command = f"{sys.executable} {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'update_social_data.py')} --hashtag \"{new_hashtag}\"")
                add_gremlin_task(task_id, update_command)

                return jsonify({'status': 'success', 'message': f'Hashtag "{new_hashtag}" added and data update queued.'}), 200
            else:
                return jsonify({'status': 'info', 'message': f'Hashtag "{new_hashtag}" already exists.'}), 200

    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': f'Config file not found at {CONFIG_FILE}'}), 500
    except json.JSONDecodeError:
        return jsonify({'status': 'error', 'message': f'Error decoding JSON from {CONFIG_FILE}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server for LearnGraph...")
    print(f"Config file path: {CONFIG_FILE}")
    app.run(port=5000, debug=True)