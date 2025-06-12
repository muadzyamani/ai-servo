import requests
import re
import json

def check_ollama_availability():
    """Check if Ollama is running and accessible."""
    try:
        # Try to ping the Ollama API
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        print("Ollama is running and accessible")
        return True
    except requests.exceptions.ConnectionError:
        print("Error: Ollama is not running or not accessible at localhost:11434")
        print("Please start Ollama and try again.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error checking Ollama availability: {e}")
        return False

def send_to_ollama(prompt_text, api_url, model):
    payload = {
        "model": model,
        "prompt": prompt_text,
        "stream": False,
        "format": "json", # Instruct Ollama to output JSON directly
        "options": {
            "temperature": 0.2,
            "num_predict": 100
        }
    }
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return None

def parse_llm_response_to_json(llm_text):
    """
    Parses a JSON command object from the LLM's response text.
    Returns a dictionary or None.
    """
    print(f"LLM Raw Response: '{llm_text}'")
    if not llm_text:
        return None

    try:
        # The 'format: "json"' parameter in send_to_ollama should ensure valid JSON.
        # This is a robust way to parse it.
        command_obj = json.loads(llm_text)
        if "command" in command_obj:
            print(f"LLM suggests command: {command_obj}")
            return command_obj
        else:
            print("LLM JSON is missing 'command' key.")
            return None
    except json.JSONDecodeError:
        print("LLM response was not valid JSON.")
        return None

def parse_command_with_keywords(user_input_raw, current_angle, min_angle, max_angle, default_step):
    """
    DEPRECATED in favor of the LLM's JSON output but kept for reference.
    This function will no longer be called in the main loop.
    """
    user_input_lower = user_input_raw.lower()
    
    # Check for specific degree commands first
    match_set_angle = re.search(r'(?:set to|move to)\s*(\d{1,3})(?:\s*degrees)?', user_input_lower)
    if match_set_angle:
        angle_val = int(match_set_angle.group(1))
        if min_angle <= angle_val <= max_angle:
            return angle_val

    # Check for relative or absolute commands
    if "open" in user_input_lower:
        if "bit" in user_input_lower or "slightly" in user_input_lower:
            return min(max_angle, current_angle + default_step)
        # "open", "open fully", "open all the way" all map to max_angle
        return max_angle

    if "close" in user_input_lower:
        if "bit" in user_input_lower or "slightly" in user_input_lower:
            return max(min_angle, current_angle - default_step)
        # "close", "close fully", "close all the way" all map to min_angle
        return min_angle
    
    # If no keywords matched
    return None

def build_llm_prompt(user_input, current_angle, min_angle, max_angle):
    # This prompt is the core of the system. It defines the "API" for the LLM.
    return f"""
You are an expert AI assistant that translates natural language commands into a structured JSON format for controlling a servo motor.
The motor's range is {min_angle} to {max_angle} degrees. The current motor angle is {current_angle} degrees.

Analyze the user's request and create a JSON object with a "command" and its required "parameters".

Available commands are:
1.  "GOTO": Move to a specific angle.
    - Parameters: "angle" (integer, {min_angle}-{max_angle}).
    - Example: "move to 90 degrees" -> {{"command": "GOTO", "angle": 90}}
    - Note: "open" means {max_angle}, "close" means {min_angle}, "middle" means 90.

2.  "ADJUST": Move by a relative amount of degrees.
    - Parameters: "degrees" (integer). Positive is clockwise (towards {max_angle}), negative is counter-clockwise (towards {min_angle}).
    - Example: "turn a little to the right" -> {{"command": "ADJUST", "degrees": 20}}
    - Example: "move 30 degrees left" -> {{"command": "ADJUST", "degrees": -30}}

3.  "SPIN": Perform full rotations back and forth.
    - Parameters: "times" (integer, number of full spins).
    - Note: This action ends at the starting angle.
    - Example: "spin 3 times" -> {{"command": "SPIN", "times": 3}}

4.  "SWEEP": Move back and forth continuously like a radar.
    - Parameters: "repetitions" (integer, number of back-and-forth sweeps).
    - Note: This action ends at the starting angle.
    - Example: "sweep back and forth 5 times" -> {{"command": "SWEEP", "repetitions": 5}}
    
5.  "NOD": Perform a "yes" motion.
    - Parameters: "times" (integer).
    - Example: "nod yes" -> {{"command": "NOD", "times": 2}}

6.  "SHAKE": Perform a "no" motion.
    - Parameters: "times" (integer).
    - Example: "shake your head" -> {{"command": "SHAKE", "times": 2}}

User Request: "{user_input}"
Current Angle: {current_angle}

Respond ONLY with the JSON object. Do not add any other text, explanation, or markdown formatting.
"""