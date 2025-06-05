import serial
import requests
import json
import time
import re # Used in parse_llm_response_for_angle

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3:mini"
SERIAL_PORT = 'COM3'
SERIAL_BAUDRATE = 9600
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
    """
    Tries to extract an angle from the LLM's response or via keyword fallback.
    """
    print(f"LLM Raw Response: '{llm_text}'")

    # Try to directly find a number in LLM's response
    match = re.search(r'\b(\d{1,3})\b', llm_text)
    if match:
        try:
            angle = int(match.group(1))
            if MOTOR_MIN_ANGLE <= angle <= MOTOR_MAX_ANGLE:
                print(f"LLM suggests angle: {angle}")
                return angle
        except ValueError:
            pass # Not a valid integer

    # Fallback: Simple keyword logic
    user_input_lower = user_input_raw.lower()
    new_angle = current_angle # Start with current angle for fallback

    # Define target angles for full open/close
    target_open_full = MOTOR_MAX_ANGLE
    target_close_full = MOTOR_MIN_ANGLE

    if "open" in user_input_lower:
        if "bit" in user_input_lower or "slightly" in user_input_lower:
            new_angle = min(MOTOR_MAX_ANGLE, current_angle + MOTOR_DEFAULT_STEP)
        elif "fully" in user_input_lower or "all the way" in user_input_lower:
            new_angle = target_open_full
        else: # Generic "open"
            new_angle = target_open_full
    elif "close" in user_input_lower:
        if "bit" in user_input_lower or "slightly" in user_input_lower:
            new_angle = max(MOTOR_MIN_ANGLE, current_angle - MOTOR_DEFAULT_STEP)
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


    if new_angle != current_angle: # Only return if fallback logic determined a change
        print(f"Fallback logic suggests angle: {new_angle}")
        return new_angle

    print("Could not determine a valid angle from LLM or keywords.")
    return None


def send_to_arduino(ser, angle_to_send):
    """
    Sends the target angle to the Arduino.
    Returns True if successful, False otherwise.
    """
    if angle_to_send is not None:
        # Ensure angle is within bounds
        angle_to_send = max(MOTOR_MIN_ANGLE, min(MOTOR_MAX_ANGLE, int(angle_to_send)))
        print(f"Sending to Arduino: {angle_to_send}")
        try:
            ser.write(f"{angle_to_send}\n".encode('utf-8'))
            time.sleep(0.1) # Give Arduino time to process
            # Read Arduino's response (optional, but good for debugging)
            response_lines = []
            while ser.in_waiting > 0:
                response_from_arduino = ser.readline().decode('utf-8', errors='ignore').strip()
                if response_from_arduino: # Only print if there's actual content
                    response_lines.append(response_from_arduino)
            if response_lines:
                print(f"Arduino: {' | '.join(response_lines)}")
            return True
        except serial.SerialException as e:
            print(f"Error writing to Arduino: {e}")
            return False
    return False

def initialize_arduino_connection(port, baudrate, initial_wait_time=2):
    """Initializes and returns the serial connection to Arduino, or None on failure."""
    try:
        arduino_ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Connected to Arduino on {port}")
        time.sleep(initial_wait_time)  # Wait for Arduino to reset and be ready
        # Read and discard any initial messages from Arduino
        while arduino_ser.in_waiting > 0:
            init_msg = arduino_ser.readline().decode('utf-8', errors='ignore').strip()
            if init_msg: # Only print if Arduino sent something meaningful
                 print(f"Arduino (init): {init_msg}")
        return arduino_ser
    except serial.SerialException as e:
        print(f"Error opening serial port {port}: {e}")
        return None

def build_llm_prompt(user_input, current_angle):
    """Constructs the prompt for the LLM."""
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

def get_angle_command(user_input, current_motor_angle_state):
    """
    Gets the target angle from LLM or fallback logic.
    Returns the target angle (int) or None.
    """
    prompt = build_llm_prompt(user_input, current_motor_angle_state)
    llm_response_text = send_to_ollama(prompt)

    target_angle = None
    if llm_response_text:
        target_angle = parse_llm_response_for_angle(llm_response_text, user_input, current_motor_angle_state)

    # If LLM didn't provide a valid angle, try fallback directly (parse_llm_response_for_angle handles this if llm_text is empty/None)
    if target_angle is None:
        print("LLM did not provide a clear angle or failed. Relying on fallback keywords...")
        target_angle = parse_llm_response_for_angle("", user_input, current_motor_angle_state) # Pass empty LLM response for pure fallback

    return target_angle


def run_cli_interaction(arduino_ser, initial_angle):
    """Runs the main command-line interface loop for motor control."""
    current_angle_local = initial_angle
    print("\nMotor Control CLI. Type 'exit' to quit.")
    print(f"Current motor angle assumed to be: {current_angle_local}")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            break
        if not user_input:
            continue

        target_angle = get_angle_command(user_input, current_angle_local)

        if target_angle is not None:
            if send_to_arduino(arduino_ser, target_angle):
                current_angle_local = target_angle # Update local state only if send was successful
                print(f"Motor command processed. New assumed angle: {current_angle_local}")
            else:
                print("Failed to send command to Arduino. Angle not updated.")
        else:
            print("AI/Fallback could not determine a valid action. Please try rephrasing.")

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