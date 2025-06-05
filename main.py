import serial
import requests
import json
import time
import re

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3:mini"
SERIAL_PORT = 'COM3'
SERIAL_BAUDRATE = 115200 # Make sure this matches Arduino
MOTOR_MIN_ANGLE = 0
MOTOR_MAX_ANGLE = 180
MOTOR_DEFAULT_STEP = 15
MOTOR_INITIAL_ANGLE = 90

# --- Helper Functions ---
def send_to_ollama(prompt_text):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt_text,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 20
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

def parse_llm_response_for_angle(llm_text, user_input_raw, current_angle):
    print(f"LLM Raw Response: '{llm_text}'")
    match = re.search(r'\b(\d{1,3})\b', llm_text)
    if match:
        try:
            angle = int(match.group(1))
            if MOTOR_MIN_ANGLE <= angle <= MOTOR_MAX_ANGLE:
                print(f"LLM suggests angle: {angle}")
                return angle
        except ValueError:
            pass
    user_input_lower = user_input_raw.lower()
    new_angle = current_angle
    target_open_full = MOTOR_MAX_ANGLE
    target_close_full = MOTOR_MIN_ANGLE
    if "open" in user_input_lower:
        if "bit" in user_input_lower or "slightly" in user_input_lower:
            new_angle = min(MOTOR_MAX_ANGLE, current_angle + MOTOR_DEFAULT_STEP)
        elif "fully" in user_input_lower or "all the way" in user_input_lower:
            new_angle = target_open_full
        else:
            new_angle = target_open_full
    elif "close" in user_input_lower:
        if "bit" in user_input_lower or "slightly" in user_input_lower:
            new_angle = max(MOTOR_MIN_ANGLE, current_angle - MOTOR_DEFAULT_STEP)
        elif "fully" in user_input_lower or "all the way" in user_input_lower:
            new_angle = target_close_full
        else:
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
    if new_angle != current_angle:
        print(f"Fallback logic suggests angle: {new_angle}")
        return new_angle
    print("Could not determine a valid angle from LLM or keywords.")
    return None

def send_command_to_arduino(ser, command_str):
    """Sends a generic command string to the Arduino."""
    try:
        print(f"Sending control command to Arduino: {command_str.strip()}")
        ser.write(f"{command_str.strip()}\n".encode('utf-8'))
        time.sleep(0.05) # Brief pause for Arduino to register command
        # Don't necessarily wait for a response for control commands unless designed
        return True
    except serial.SerialException as e:
        print(f"Error writing control command to Arduino: {e}")
        return False

def send_angle_to_arduino(ser, angle_to_send):
    """Sends the target angle to the Arduino."""
    if angle_to_send is not None:
        angle_to_send = max(MOTOR_MIN_ANGLE, min(MOTOR_MAX_ANGLE, int(angle_to_send)))
        print(f"Sending angle to Arduino: {angle_to_send}")
        try:
            ser.write(f"{angle_to_send}\n".encode('utf-8'))
            time.sleep(0.1)
            response_lines = []
            while ser.in_waiting > 0:
                response_from_arduino = ser.readline().decode('utf-8', errors='ignore').strip()
                if response_from_arduino:
                    response_lines.append(response_from_arduino)
            if response_lines:
                print(f"Arduino: {' | '.join(response_lines)}")
            return True
        except serial.SerialException as e:
            print(f"Error writing angle to Arduino: {e}")
            return False
    return False

def initialize_arduino_connection(port, baudrate, initial_wait_time=2):
    try:
        arduino_ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Connected to Arduino on {port}")
        time.sleep(initial_wait_time)
        while arduino_ser.in_waiting > 0:
            init_msg = arduino_ser.readline().decode('utf-8', errors='ignore').strip()
            if init_msg:
                 print(f"Arduino (init): {init_msg}")
        return arduino_ser
    except serial.SerialException as e:
        print(f"Error opening serial port {port}: {e}")
        return None

def build_llm_prompt(user_input, current_angle):
    return f"""
You are an AI assistant controlling a servo motor with a range of {MOTOR_MIN_ANGLE} to {MOTOR_MAX_ANGLE} degrees.
The current motor angle is {current_angle} degrees.
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
Current Angle: {current_angle}
New Target Angle (JUST THE NUMBER):
"""

# WIP: Need to refine this function
def get_angle_command_from_keywords(user_input_raw, current_angle):
    user_input_lower = user_input_raw.lower()
    new_angle = None
    if "open fully" in user_input_lower or "open all the way" in user_input_lower: new_angle = MOTOR_MAX_ANGLE
    elif "close fully" in user_input_lower or "close all the way" in user_input_lower: new_angle = MOTOR_MIN_ANGLE
    elif "open a bit" in user_input_lower or "open slightly" in user_input_lower: new_angle = min(MOTOR_MAX_ANGLE, current_angle + MOTOR_DEFAULT_STEP)
    elif "close a bit" in user_input_lower or "close slightly" in user_input_lower: new_angle = max(MOTOR_MIN_ANGLE, current_angle - MOTOR_DEFAULT_STEP)
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

def get_angle_command(user_input, current_motor_angle_state, arduino_ser): # Pass arduino_ser
    """
    Gets the target angle from keywords first, then LLM fallback.
    Returns the target angle (int) or None.
    """
    target_angle = get_angle_command_from_keywords(user_input, current_motor_angle_state)
    if target_angle is not None:
        return target_angle

    # If no keyword match, then use LLM
    print("No direct keyword match. Querying LLM...")
    send_command_to_arduino(arduino_ser, "THINKING_START") # TELL ARDUINO TO START ANIMATION

    prompt = build_llm_prompt(user_input, current_motor_angle_state)
    llm_response_text = send_to_ollama(prompt)

    # The angle command sent later will implicitly stop the "thinking" animation on Arduino

    if llm_response_text:
        target_angle = parse_llm_response_for_angle(llm_response_text, user_input, current_motor_angle_state)

    if target_angle is None:
        if llm_response_text:
             print("LLM did not provide a clear angle. Trying LLM response with fallback keywords...")
             target_angle = parse_llm_response_for_angle(llm_response_text, user_input, current_motor_angle_state)
        else:
            print("LLM failed or no response, and no keyword match. Relying on basic fallback...")
            target_angle = parse_llm_response_for_angle("", user_input, current_motor_angle_state)
    return target_angle


def run_cli_interaction(arduino_ser, initial_angle):
    current_angle_local = initial_angle
    print("\nMotor Control CLI. Type 'exit' to quit.")
    print(f"Current motor angle assumed to be: {current_angle_local}")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            break
        if not user_input:
            continue

        target_angle = get_angle_command(user_input, current_angle_local, arduino_ser)

        if target_angle is not None:
            if send_angle_to_arduino(arduino_ser, target_angle):
                current_angle_local = target_angle
                print(f"Motor command processed. New assumed angle: {current_angle_local}")
            else:
                print("Failed to send command to Arduino. Angle not updated.")
                send_command_to_arduino(arduino_ser, "IDLE_STATE")
        else:
            print("AI/Fallback could not determine a valid action. Please try rephrasing.")
            send_command_to_arduino(arduino_ser, "IDLE_STATE")

# --- Main Execution ---
if __name__ == "__main__":
    arduino_connection = initialize_arduino_connection(SERIAL_PORT, SERIAL_BAUDRATE)

    if arduino_connection:
        current_motor_angle_main = MOTOR_INITIAL_ANGLE
        try:
            run_cli_interaction(arduino_connection, current_motor_angle_main)
        except KeyboardInterrupt:
            print("\nExiting due to user interruption...")
        finally:
            print("Closing Arduino connection...")
            if arduino_connection.is_open:
                arduino_connection.close()
            print("Connection closed.")
    else:
        print("Failed to connect to Arduino. Exiting.")
    print("Program finished.")