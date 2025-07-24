import os
import time
import json
import subprocess
import threading
import sys
import datetime

# Get the absolute path of the script and project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..')

INSTRUCTION_FILE = os.path.join(project_root, 'gremlin_instructions.json')
RESULT_FILE = os.path.join(project_root, 'gremlin_results.json')

def execute_task(task_id, command):
    print(f"Gremlin: Executing task {task_id} with command: {command}")
    result = {
        'task_id': task_id,
        'status': 'running',
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    try:
        # Always pass the command as a single string when shell=True
        process = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        result['stdout'] = process.stdout
        result['stderr'] = process.stderr
        result['returncode'] = process.returncode
        result['status'] = 'completed' if process.returncode == 0 else 'failed'
    except Exception as e:
        result['status'] = 'error'
        result['stderr'] = str(e)
    finally:
        result['timestamp'] = datetime.datetime.now().isoformat()
        write_result(result)
        print(f"Gremlin: Task {task_id} finished with status: {result['status']}")

def write_result(result):
    results = []
    if os.path.exists(RESULT_FILE):
        try:
            with open(RESULT_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except json.JSONDecodeError:
            pass # File might be empty or corrupted, start fresh
    
    results.append(result)
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def gremlin_loop():
    print("Gremlin: Starting instruction loop...")
    while True:
        print(f"Gremlin: Checking for instructions at {INSTRUCTION_FILE}")
        if os.path.exists(INSTRUCTION_FILE):
            try:
                with open(INSTRUCTION_FILE, 'r', encoding='utf-8') as f:
                    instructions = json.load(f)
                
                if instructions:
                    # Take the first instruction
                    instruction = instructions.pop(0)
                    task_id = instruction.get('task_id', 'unknown')
                    command = instruction.get('command')

                    if command:
                        # Write remaining instructions back to file
                        with open(INSTRUCTION_FILE, 'w', encoding='utf-8') as f:
                            json.dump(instructions, f, indent=2)
                        
                        # Execute task in a new thread to keep the loop responsive
                        task_thread = threading.Thread(target=execute_task, args=(task_id, command))
                        task_thread.start()
                    else:
                        print(f"Gremlin: Invalid instruction (missing command) for task {task_id}. Skipping.")
                        # If invalid, still remove it from the queue
                        with open(INSTRUCTION_FILE, 'w', encoding='utf-8') as f:
                            json.dump(instructions, f, indent=2)
                else:
                    # Instruction file is empty, delete it
                    os.remove(INSTRUCTION_FILE)
            except json.JSONDecodeError:
                print("Gremlin: Error decoding instruction file. Deleting to prevent loop.")
                os.remove(INSTRUCTION_FILE)
            except Exception as e:
                print(f"Gremlin: An unexpected error occurred: {e}")
        
        time.sleep(1) # Check for new instructions every second

if __name__ == "__main__":
    gremlin_loop()