from flask import Flask, render_template, request, jsonify
import serial
import requests
import json
import time
import re
import threading # For managing Arduino connection

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3:mini"
SERIAL_PORT = 'COM3'
SERIAL_BAUDRATE = 115200
MOTOR_MIN_ANGLE = 0
MOTOR_MAX_ANGLE = 180
MOTOR_DEFAULT_STEP = 15
MOTOR_INITIAL_ANGLE = 90

# --- Global variables for Arduino and motor state ---
arduino_ser = None
current_motor_angle = MOTOR_INITIAL_ANGLE # Initialize with default
arduino_lock = threading.Lock() # To prevent concurrent access to Arduino

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Helper Functions ---
def send_to_ollama(prompt_text):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt_text,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 20 # Max tokens to predict, we only need a number
        }
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return None

def parse_llm_response_for_angle(llm_text, user_input_raw, current_angle_param): # Renamed current_angle to avoid conflict
    print(f"LLM Raw Response: '{llm_text}'")
    match = re.search(r'\b(\d{1,3})\b', llm_text) # Look for 1 to 3 digits
    if match:
        try:
            angle = int(match.group(1))
            if MOTOR_MIN_ANGLE <= angle <= MOTOR_MAX_ANGLE:
                print(f"LLM suggests angle: {angle}")
                return angle
        except ValueError:
            pass # Not a valid integer

    user_input_lower = user_input_raw.lower()
    new_angle = current_angle_param

    # Define target angles for full open/close
    target_open_full = MOTOR_MAX_ANGLE
    target_close_full = MOTOR_MIN_ANGLE

    if "open" in user_input_lower:
        if "bit" in user_input_lower or "slightly" in user_input_lower:
            new_angle = min(MOTOR_MAX_ANGLE, current_angle_param + MOTOR_DEFAULT_STEP)
        elif "fully" in user_input_lower or "all the way" in user_input_lower:
            new_angle = target_open_full
        else: # Generic "open"
            new_angle = target_open_full
    elif "close" in user_input_lower:
        if "bit" in user_input_lower or "slightly" in user_input_lower:
            new_angle = max(MOTOR_MIN_ANGLE, current_angle_param - MOTOR_DEFAULT_STEP)
        elif "fully" in user_input_lower or "all the way" in user_input_lower:
            new_angle = target_close_full
        else: # Generic "close"
            new_angle = target_close_full
    elif "set to" in user_input_lower or "move to" in user_input_lower:
        match_angle_val = re.search(r'\b(\d{1,3})\b', user_input_lower)
        if match_angle_val:
            try:
                angle_val = int(match_angle_val.group(1))
                if MOTOR_MIN_ANGLE <= angle_val <= MOTOR_MAX_ANGLE:
                    new_angle = angle_val
            except ValueError:
                pass

    if new_angle != current_angle_param: # Only return if fallback logic determined a change
        print(f"Fallback logic suggests angle: {new_angle}")
        return new_angle

    print("Could not determine a valid angle from LLM or keywords.")
    return None

def build_llm_prompt(user_input, current_angle_param): # Renamed current_angle
    return f"""
You are an AI assistant controlling a servo motor with a range of {MOTOR_MIN_ANGLE} to {MOTOR_MAX_ANGLE} degrees.
The current motor angle is {current_angle_param} degrees.
0 degrees means 'fully closed'. 180 degrees means 'fully open'.
The user wants to: "{user_input}"
Based on the user's request and the current angle, what should the new target angle be?
If the user wants to return to the default or initial condition, assume {MOTOR_INITIAL_ANGLE} degrees.
If the user says "a bit" or "slightly", adjust by approximately {MOTOR_DEFAULT_STEP} degrees.
If the user says "open", unless specified otherwise, assume "fully open" ({MOTOR_MAX_ANGLE} degrees).
If the user says "close", unless specified otherwise, assume "fully closed" ({MOTOR_MIN_ANGLE} degrees).
Respond ONLY with the integer number for the new target angle. For example: 90 or 0 or 180 or 15.
Do not add any other text, explanation, or punctuation. Just the number.
User: "{user_input}"
Current Angle: {current_angle_param}
New Target Angle (JUST THE NUMBER):
"""

def get_angle_command_from_keywords(user_input_raw, current_angle_param): # Renamed current_angle
    user_input_lower = user_input_raw.lower()
    new_angle = None # Important: only set if a keyword rule applies
    if "open fully" in user_input_lower or "open all the way" in user_input_lower: new_angle = MOTOR_MAX_ANGLE
    elif "close fully" in user_input_lower or "close all the way" in user_input_lower: new_angle = MOTOR_MIN_ANGLE
    elif "open a bit" in user_input_lower or "open slightly" in user_input_lower: new_angle = min(MOTOR_MAX_ANGLE, current_angle_param + MOTOR_DEFAULT_STEP)
    elif "close a bit" in user_input_lower or "close slightly" in user_input_lower: new_angle = max(MOTOR_MIN_ANGLE, current_angle_param - MOTOR_DEFAULT_STEP)
    elif "open" in user_input_lower and not ("bit" in user_input_lower or "slightly" in user_input_lower): new_angle = MOTOR_MAX_ANGLE
    elif "close" in user_input_lower and not ("bit" in user_input_lower or "slightly" in user_input_lower): new_angle = MOTOR_MIN_ANGLE
    match_set_angle = re.search(r'(?:set to|move to)\s*(\d{1,3})(?:\s*degrees)?', user_input_lower)
    if match_set_angle:
        try:
            angle_val = int(match_set_angle.group(1))
            if MOTOR_MIN_ANGLE <= angle_val <= MOTOR_MAX_ANGLE: new_angle = angle_val
        except ValueError: pass
    if new_angle is not None:
        print(f"Keyword match suggests angle: {new_angle}")
        return new_angle
    return None

# --- Arduino Communication Function ---
def send_arduino_command(command_str):
    global arduino_ser
    if not arduino_ser or not arduino_ser.is_open:
        print("Arduino not connected or port not open.")
        return False
    with arduino_lock: # Ensure exclusive access
        try:
            print(f"Sending to Arduino: {command_str.strip()}")
            arduino_ser.write(f"{command_str.strip()}\n".encode('utf-8'))
            time.sleep(0.05) # Brief pause
            # For angle commands, Arduino sketch will send back "Motor moved to: X"
            # For THINKING_START, IDLE_STATE, no specific response expected by this func
            return True
        except serial.SerialException as e:
            print(f"Error writing to Arduino: {e}")
            # Attempt to reconnect or flag error
            reinitialize_arduino()
            return False
        except Exception as e:
            print(f"Unexpected error sending to Arduino: {e}")
            return False

# --- Core Logic Function ---
def process_user_command(user_input):
    global current_motor_angle # We need to update this
    
    # 1. Try keyword spotting first
    target_angle = get_angle_command_from_keywords(user_input, current_motor_angle)
    
    if target_angle is not None:
        if send_arduino_command(str(target_angle)):
            current_motor_angle = target_angle
            return {"status": "success", "message": f"Keyword: Motor moved to {target_angle}°", "angle": target_angle}
        else:
            return {"status": "error", "message": "Failed to send keyword command to Arduino", "angle": current_motor_angle}

    # 2. If no keyword match, then use LLM
    print("No direct keyword match. Querying LLM...")
    if not send_arduino_command("THINKING_START"):
         return {"status": "error", "message": "Failed to send THINKING_START to Arduino", "angle": current_motor_angle}

    prompt = build_llm_prompt(user_input, current_motor_angle)
    llm_response_text = send_to_ollama(prompt)

    if llm_response_text:
        target_angle = parse_llm_response_for_angle(llm_response_text, user_input, current_motor_angle)
    
    if target_angle is not None:
        if send_arduino_command(str(target_angle)):
            current_motor_angle = target_angle
            return {"status": "success", "message": f"LLM: Motor moved to {target_angle}°", "angle": target_angle}
        else:
            # If sending the angle fails, Arduino might still be in THINKING. Tell it to go IDLE.
            send_arduino_command("IDLE_STATE")
            return {"status": "error", "message": "LLM determined angle, but failed to send to Arduino", "angle": current_motor_angle}
    else:
        # LLM failed to determine an angle
        send_arduino_command("IDLE_STATE") # Tell Arduino to stop thinking
        return {"status": "error", "message": "LLM could not determine a valid angle.", "angle": current_motor_angle}


# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html', current_angle=current_motor_angle)

@app.route('/send_command', methods=['POST'])
def handle_send_command():
    data = request.get_json()
    user_command = data.get('command')
    if not user_command:
        return jsonify({"status": "error", "message": "No command provided"}), 400

    print(f"Received web command: {user_command}")
    result = process_user_command(user_command)
    return jsonify(result)

@app.route('/get_status', methods=['GET'])
def get_status():
    global current_motor_angle
    # In a real app, you might read this from Arduino or a more robust state
    return jsonify({"status": "success", "current_angle": current_motor_angle})

# --- Arduino Initialization and Management ---
def initialize_arduino():
    global arduino_ser
    global current_motor_angle
    try:
        print(f"Attempting to connect to Arduino on {SERIAL_PORT}...")
        arduino_ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=1)
        time.sleep(2) # Wait for Arduino to reset
        # Clear any initial messages
        while arduino_ser.in_waiting > 0:
            init_msg = arduino_ser.readline().decode('utf-8', errors='ignore').strip()
            if init_msg: print(f"Arduino (init): {init_msg}")
        
        print(f"Successfully connected to Arduino. Initial angle: {current_motor_angle}")
        return True
    except serial.SerialException as e:
        print(f"Error opening serial port {SERIAL_PORT}: {e}")
        arduino_ser = None
        return False

def reinitialize_arduino():
    global arduino_ser
    if arduino_ser and arduino_ser.is_open:
        try:
            arduino_ser.close()
        except:
            pass
    arduino_ser = None
    print("Attempting to reinitialize Arduino connection...")
    return initialize_arduino()
    

def check_ollama_service():
    """Check if Ollama is running and accessible."""
    try:
        requests.get("http://localhost:11434/api/tags", timeout=3).raise_for_status()
        print("Ollama service is accessible.")
        return True
    except requests.exceptions.RequestException:
        print("Error: Ollama service is not accessible at http://localhost:11434.")
        print("Please ensure Ollama is running.")
        return False

# --- Main Execution (for Flask) ---
if __name__ == '__main__':
    if not check_ollama_service():
        print("Exiting application.")
        exit(1)
        
    if not initialize_arduino():
        print("Failed to initialize Arduino. Web app might not control the motor.") 

    # By default, Flask runs on http://127.0.0.1:5000/
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False) # host='0.0.0.0' makes it accessible on your network