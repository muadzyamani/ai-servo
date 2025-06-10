import time
import config as cfg
from voice import listen_for_voice_command_google
from arduino import ArduinoController, CMD_THINKING_START, CMD_IDLE_STATE, CMD_RESET_STATE, CMD_SHUTDOWN
from llm import (
    build_llm_prompt,
    check_ollama_availability,
    parse_command_with_keywords,
    parse_angle_from_llm_text,
    send_to_ollama
)

class LlmServoControl:
    """Orchestrates the voice-controlled motor application."""
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

    def get_target_angle(self, user_input):
        """
        Determines the target angle from user input.
        Tries fast keyword parsing first, then falls back to the LLM.
        """
        # 1. Try fast, reliable keyword-based parsing
        target_angle = parse_command_with_keywords(
            user_input, self.current_angle, cfg.MOTOR_MIN_ANGLE, cfg.MOTOR_MAX_ANGLE, cfg.MOTOR_DEFAULT_STEP
        )
        if target_angle is not None:
            print(f"Keyword match suggests angle: {target_angle}")
            return target_angle

        # 2. If no keyword match, use the LLM as a fallback
        print("No direct keyword match. Querying LLM...")
        self.arduino.send_command(CMD_THINKING_START)

        prompt = build_llm_prompt(
            user_input, self.current_angle, cfg.MOTOR_MIN_ANGLE, cfg.MOTOR_MAX_ANGLE, 
            cfg.MOTOR_DEFAULT_STEP, cfg.MOTOR_INITIAL_ANGLE
        )
        llm_response_text = send_to_ollama(prompt, cfg.OLLAMA_API_URL, cfg.OLLAMA_MODEL)

        if llm_response_text:
            return parse_angle_from_llm_text(llm_response_text, cfg.MOTOR_MIN_ANGLE, cfg.MOTOR_MAX_ANGLE)
        
        print("LLM failed or did not provide a valid angle.")
        return None

    def run(self):
        """The main application loop for user interaction."""
        print("\nMotor Control CLI. Type 'speech' for voice, 'reset' for default, or 'exit' to quit.")
        print(f"Current motor angle assumed to be: {self.current_angle}")

        while True:
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

            target_angle = self.get_target_angle(user_input)

            if target_angle is not None:
                if self.arduino.set_angle(target_angle, cfg.MOTOR_MIN_ANGLE, cfg.MOTOR_MAX_ANGLE):
                    self.current_angle = target_angle
                    print(f"Motor command processed. New assumed angle: {self.current_angle}")
                else:
                    print("Failed to send command to Arduino. Angle not updated.")
                    self.arduino.send_command(CMD_IDLE_STATE)
            else:
                print("AI/Keywords could not determine a valid action. Please try rephrasing.")
                self.arduino.send_command(CMD_IDLE_STATE)
                
    def shutdown(self):
        """Properly closes resources."""
        self.arduino.disconnect()
        print("Program finished.")


# --- Main Execution ---
if __name__ == "__main__":
    app = LlmServoControl()
    
    if app.setup():
        try:
            app.run()
        except KeyboardInterrupt:
            print("\nExiting due to user interruption...")
        finally:
            app.shutdown()