import requests
import re
import json
import time

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
        # 1. CAPTURE START TIME
        start_time = time.time()

        response = requests.post(api_url, json=payload, timeout=30)
        response.raise_for_status()

        # 2. CALCULATE LATENCY
        latency = time.time() - start_time
        
        response_data = response.json()
        
        # 3. EXTRACT TOKEN COUNTS AND CREATE A STATS DICT
        # Ollama provides detailed timing and token counts in its response
        stats = {
            "latency_sec": round(latency, 2),
            "prompt_tokens": response_data.get("prompt_eval_count", 0),
            "response_tokens": response_data.get("eval_count", 0),
            "total_duration_ms": response_data.get("total_duration", 0) / 1_000_000, # Convert nanoseconds to ms
            "load_duration_ms": response_data.get("load_duration", 0) / 1_000_000,
            "prompt_eval_duration_ms": response_data.get("prompt_eval_duration", 0) / 1_000_000,
            "eval_duration_ms": response_data.get("eval_duration", 0) / 1_000_000
        }
        
        # 4. RETURN THE RESPONSE AND THE STATS
        return response_data.get("response", "").strip(), stats

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        # Return None for both values in case of an error
        return None, None

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
    You are a JSON API for a servo motor.
    Motor range: {min_angle}-{max_angle}. Current angle: {current_angle}.
    Convert the user request to a JSON object.

    COMMANDS & EXAMPLES:
    - "GOTO": Move to absolute angle. Ex: "go to 90" -> {{"command": "GOTO", "angle": 90}}
    - "ADJUST": Move by relative degrees. Ex: "turn right a bit" -> {{"command": "ADJUST", "degrees": 20}}
    - "SPIN": Full rotations. Ex: "spin twice" -> {{"command": "SPIN", "times": 2}}
    - "SWEEP": Scan side-to-side. Ex: "sweep the area" -> {{"command": "SWEEP", "repetitions": 1}}
    - "NOD": "Yes" motion. Ex: "nod yes" -> {{"command": "NOD", "times": 2}}
    - "SHAKE": "No" motion. Ex: "shake no" -> {{"command": "SHAKE", "times": 2}}

    Request: "{user_input}"

    Respond ONLY with the JSON object.
    """