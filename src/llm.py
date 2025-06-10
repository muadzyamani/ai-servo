import requests
import re

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
        "options": {
            "temperature": 0.2,
            "num_predict": 20
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

def parse_angle_from_llm_text(llm_text, min_angle, max_angle):
    """
    Parses a numeric angle from the LLM's response text.
    Returns an integer angle or None.
    """
    print(f"LLM Raw Response: '{llm_text}'")
    if not llm_text:
        return None
        
    match = re.search(r'\b(\d{1,3})\b', llm_text)
    if match:
        try:
            angle = int(match.group(1))
            if min_angle <= angle <= max_angle:
                print(f"LLM suggests angle: {angle}")
                return angle
            else:
                print(f"LLM angle {angle} is out of range ({min_angle}-{max_angle}).")
        except ValueError:
            pass # Should not happen with this regex, but good practice
    return None

def parse_command_with_keywords(user_input_raw, current_angle, min_angle, max_angle, default_step):
    """
    Determines a target angle based on keywords in the user's input.
    This is the fast, non-LLM method.
    Returns an integer angle or None.
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

def build_llm_prompt(user_input, current_angle, min_angle, max_angle, default_step, initial_angle):
    return f"""
        You are an AI assistant controlling a servo motor with a range of {min_angle} to {max_angle} degrees.
        The current motor angle is {current_angle} degrees.
        0 degrees means 'fully closed'. 180 degrees means 'fully open'.
        The user wants to: "{user_input}"
        Based on the user's request and the current angle, what should the new target angle be?
        If the user wants to return to the default or initial condition, assume {initial_angle} degrees.
        If the user says "a bit" or "slightly", adjust by approximately {default_step} degrees.
        If the user says "open", unless specified otherwise, assume "fully open" ({max_angle} degrees).
        If the user says "close", unless specified otherwise, assume "fully closed" ({min_angle} degrees).
        Respond ONLY with the integer number for the new target angle. For example: 90 or 0 or 180 or 15.
        Do not add any other text, explanation, or punctuation. Just the number.
        User: "{user_input}"
        Current Angle: {current_angle}
        New Target Angle (JUST THE NUMBER):
        """