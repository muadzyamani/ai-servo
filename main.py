import time
import src.config as cfg
from src.voice import listen_for_voice_command_google
from src.arduino import (
    ArduinoController, CMD_THINKING_START, CMD_IDLE_STATE,
    CMD_RESET_STATE, CMD_SHUTDOWN, CMD_AWAIT_AUTH, CMD_AUTH_SUCCESS, CMD_AUTH_FAIL
)
from src.llm import (
    build_llm_prompt,
    check_ollama_availability,
    parse_command_with_keywords,
    parse_llm_response_to_json,
    send_to_ollama
)

class LlmServoControl:
    """Manages the LLM-controlled motor application."""
    def __init__(self):
        self.current_angle = cfg.MOTOR_INITIAL_ANGLE
        self.arduino = ArduinoController(cfg.SERIAL_PORT, cfg.SERIAL_BAUDRATE)

    def setup(self):
        """Initializes system checks and connections. Returns True on success."""
        print("Checking system dependencies...")
        if not check_ollama_availability():
            print("Exiting. Please start Ollama and try again.")
            return False
        
        if not self.arduino.connect():
            print("Failed to connect to Arduino. Exiting.")
            return False
            
        return True

    def authenticate(self):
        """
        Handles the RFID authentication flow before starting the main app.
        Returns True on success, False on failure/timeout.
        """
        # Check if authentication is bypassed
        if cfg.BYPASS_RFID_AUTH:
            print("\n--- Authentication Bypassed (Testing Mode) ---")
            print("RFID authentication is disabled in config.")
            print("Proceeding directly to motor control...")
            # Still send auth success to Arduino for consistent LCD display
            self.arduino.send_command(CMD_AUTH_SUCCESS)
            time.sleep(2) # Give Arduino time to display the message
            return True
        
        print("\n--- Awaiting Authentication ---")
        print("Please scan an authorized RFID card on the reader.")
        self.arduino.send_command(CMD_AWAIT_AUTH)

        # Define the correct, full prefix the Arduino sends
        auth_prefix = "Card detected for auth! UID:"

        while True: # Loop to allow multiple scan attempts
            # Wait for the correct prefix
            uid = self.arduino.wait_for_response(auth_prefix, timeout=60)

            if uid is None:
                print("\nAuthentication timed out. No card scanned.")
                return False

            uid_lower = uid.lower()

            # --- DEBUGGING LINES ---
            # print(f"DEBUG: Checking for UID: '{uid_lower}'")
            # print(f"DEBUG: Available keys in config: {list(cfg.AUTHORIZED_UIDS.keys())}")
            # --- END OF DEBUGGING LINES ---

            if uid_lower in cfg.AUTHORIZED_UIDS:
                user = cfg.AUTHORIZED_UIDS[uid_lower]
                print(f"Authentication successful! Welcome, {user}.")
                self.arduino.send_command(CMD_AUTH_SUCCESS)
                time.sleep(2) # Give Arduino time to display the message
                return True
            else:
                print(f"Unauthorized card scanned (UID: {uid}). Please try again.")
                self.arduino.send_command(CMD_AUTH_FAIL)

    def get_llm_command(self, user_input):
        """
        Determines the target command from user input by querying the LLM.
        """
        print("Querying LLM for structured command...")
        self.arduino.send_command(CMD_THINKING_START)

        prompt = build_llm_prompt(
            user_input, self.current_angle, cfg.MOTOR_MIN_ANGLE, cfg.MOTOR_MAX_ANGLE
        )
        llm_response_text = send_to_ollama(prompt, cfg.OLLAMA_API_URL, cfg.OLLAMA_MODEL)

        if llm_response_text:
            return parse_llm_response_to_json(llm_response_text)
        
        print("LLM failed or did not provide a valid command.")
        return None
    
    def display_command_help(self):
        """Prints a formatted help screen with available commands and examples."""
        # ... (This function remains unchanged)
        print("\n--- Available Commands & Examples ---")
        print("The AI can interpret a wide range of natural language phrases.")
        print("Here are the primary actions it can perform:\n")
        
        commands = [
            {"name": "GOTO", "desc": "Move to a specific angle.", "example": "'set to 45 degrees', 'go to 180'"},
            {"name": "ADJUST", "desc": "Turn by a relative amount.", "example": "'turn a little to the right', 'move left by 20 deg'"},
            {"name": "SPIN", "desc": "Rotate back and forth rapidly.", "example": "'spin around a few times', 'do a spin'"},
            {"name": "SWEEP", "desc": "Scan smoothly side-to-side.", "example": "'sweep the area', 'look around'"},
            {"name": "NOD", "desc": "Perform a 'yes' motion.", "example": "'nod your head', 'nod yes twice'"},
            {"name": "SHAKE", "desc": "Perform a chaotic 'no' motion.", "example": "'shake your head no', 'shake it'"},
        ]
        
        # Using f-strings for nice alignment
        for cmd in commands:
            print(f"  - {cmd['name']:<7} : {cmd['desc']:<35} e.g., {cmd['example']}")
            
        print("\n--- Special Keywords ---")
        print("  - speech  : Activate voice command mode.")
        print("  - reset   : Reset the motor and the Arduino's display.")
        print("  - exit    : Shut down the system gracefully.")
        print("  - commands: Display this help message.")
        print("-" * 37 + "\n")

    def run(self):
        """The main application loop for user interaction."""
        print("\nMotor Control CLI. Type 'speech' for voice, 'reset' for default, 'help' for list of commands or 'exit' to quit.")
        print(f"Current motor angle assumed to be: {self.current_angle}")

        while True:
            # ... (The rest of this function remains unchanged)
            mode_input = input("You: ").strip()

            if mode_input.lower() == 'speech':
                user_input = listen_for_voice_command_google()
            else:
                user_input = mode_input

            if not user_input:
                print("No valid command received. Please try again.")
                continue
            
            if user_input.lower() == 'exit':
                self.arduino.send_command(CMD_SHUTDOWN)
                time.sleep(1) # Give it a moment
                break

            if user_input.lower() == 'reset':
                print("System resetting. Motor returning to default.")
                self.arduino.send_command(CMD_RESET_STATE)
                self.current_angle = cfg.MOTOR_INITIAL_ANGLE
                print(f"Angle state reset to: {self.current_angle}")
                continue

            if user_input.lower() == 'help':
                self.display_command_help()
                continue

            command_dict = self.get_llm_command(user_input)

            if command_dict and "command" in command_dict:
                cmd = command_dict.get("command")

                # Python-side logic to handle state changes
                new_angle = None
                
                # Pre-process ADJUST command into a GOTO command
                if cmd == "ADJUST":
                    degrees = command_dict.get("degrees", 0)
                    target_angle = self.current_angle + degrees
                    # Clamp the angle to the valid range
                    clamped_angle = max(cfg.MOTOR_MIN_ANGLE, min(cfg.MOTOR_MAX_ANGLE, target_angle))
                    # Mutate the command to a simple GOTO for the Arduino
                    command_dict = {"command": "GOTO", "angle": clamped_angle}
                    print(f"Translated ADJUST to GOTO: {command_dict}")

                # Update local angle state if it's a command that sets a final angle
                if command_dict.get("command") == "GOTO":
                    new_angle = command_dict.get("angle")

                # Send the final command to Arduino
                if self.arduino.send_json_command(command_dict):
                    if new_angle is not None:
                        self.current_angle = new_angle
                        print(f"Motor command sent. New assumed angle: {self.current_angle}")
                    else: # For commands like SPIN or SWEEP that return to start
                        print(f"Sequence command '{cmd}' sent. Angle remains: {self.current_angle}")
                else:
                    print("Failed to send command to Arduino. Angle not updated.")
                    self.arduino.send_command(CMD_IDLE_STATE)
            else:
                print("AI could not determine a valid action. Please try rephrasing.")
                self.arduino.send_command(CMD_IDLE_STATE)
                
    def shutdown(self):
        """Properly closes resources."""
        self.arduino.disconnect()
        print("Program finished.")


# --- Main Execution ---
if __name__ == "__main__":
    app = LlmServoControl()
    
    if app.setup():
        print("\n-------------------------------------------")
        print("System connected. Arduino is in idle mode.")
        
        # Show different prompts based on authentication mode
        if cfg.BYPASS_RFID_AUTH:
            print("RFID Authentication: DISABLED (Testing Mode)")
            print("Type 'begin' to start motor control.")
        else:
            print("RFID Authentication: ENABLED")
            print("Type 'begin' to start authentication.")
        
        print("-------------------------------------------")
        while True:
            command = input("> ").strip().lower()
            if command == 'begin':
                break
            else:
                print("Invalid command. Please type 'begin' to continue.")

        if app.authenticate():
            try:
                app.run()
            except KeyboardInterrupt:
                print("\nExiting due to user interruption...")
            finally:
                app.shutdown()
        else:
            print("Authentication failed. Shutting down.")
            app.shutdown()