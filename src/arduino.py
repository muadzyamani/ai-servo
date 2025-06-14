import serial
import time
import json
import src.config as cfg

CMD_THINKING_START = "THINKING_START"
CMD_IDLE_STATE = "IDLE_STATE"
CMD_RESET_STATE = "RESET_STATE"
CMD_SHUTDOWN = "SHUTDOWN_CMD"

class ArduinoController:
    """
    Manages serial communication with the Arduino.
    Can operate in a 'mock' mode for testing without hardware.
    """
    def __init__(self, port, baudrate, initial_wait_time=2):
        self.port = port
        self.baudrate = baudrate
        self.initial_wait_time = initial_wait_time
        self.ser = None

        self.mock_mode = cfg.USE_MOCK_ARDUINO
        self._is_mock_connected = False # State for the mock connection
        if self.mock_mode:
            print("-" * 50)
            print("--- ARDUINO CONTROLLER IS IN MOCK MODE ---")
            print("--- No hardware connection will be attempted. ---")
            print("-" * 50)
    
    def connect(self):
        """Establishes the serial connection or simulates it if in mock mode."""
        #
        if self.mock_mode:
            print(f"MOCK: Simulating connection to Arduino on {self.port}...")
            self._is_mock_connected = True
            time.sleep(0.5) # Simulate a small delay
            print("MOCK: Connection successful.")
            return True

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to Arduino on {self.port}")
            time.sleep(self.initial_wait_time) # Wait for Arduino to reset
            self._clear_initial_buffer()
            return True
        except serial.SerialException as e:
            print(f"Error opening serial port {self.port}: {e}")
            self.ser = None
            return False
        
    def _clear_initial_buffer(self):
        """Clears any startup messages from the Arduino buffer."""
        if not self.is_connected():
            return
        # This check prevents trying to access self.ser in mock mode
        if self.mock_mode:
            return
        while self.ser.in_waiting > 0:
            init_msg = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if init_msg:
                    print(f"Arduino (init): {init_msg}")

    def is_connected(self):
        """Checks if the serial connection is active or if mock connection is up."""
        if self.mock_mode:
            return self._is_mock_connected
        
        return self.ser and self.ser.is_open

    def send_command(self, command_str):
        """Sends a generic command string or simulates it."""
        if not self.is_connected():
            print("Cannot send command: Arduino not connected.")
            return False
        
        if self.mock_mode:
            print(f"MOCK: Sending control command to Arduino: {command_str}")
            print("MOCK Arduino: OK") 
            return True

        try:
            print(f"Sending control command to Arduino: {command_str}")
            self.ser.write(f"{command_str.strip()}\n".encode('utf-8'))
            time.sleep(0.05)
            self._read_response()
            return True
        except serial.SerialException as e:
            print(f"Error writing control command to Arduino: {e}")
            return False

    def send_json_command(self, command_dict):
        """Serializes a dictionary to a JSON string and sends it, or simulates it."""
        if not self.is_connected():
            print("Cannot send command: Arduino not connected.")
            return False
        
        json_string = json.dumps(command_dict)
        

        if self.mock_mode:
            print(f"MOCK: Sending JSON command to Arduino: {json_string}")
            print("MOCK Arduino: JSON_RECEIVED")
            return True

        try:
            print(f"Sending JSON command to Arduino: {json_string}")
            self.ser.write(f"{json_string}\n".encode('utf-8'))
            time.sleep(0.1)
            self._read_response()
            return True
        except (serial.SerialException, TypeError) as e:
            print(f"Error writing JSON command to Arduino: {e}")
            return False

    def set_angle(self, angle, min_angle, max_angle):
        clamped_angle = max(min_angle, min(max_angle, int(angle)))
        command_dict = {"command": "GOTO", "angle": clamped_angle}
        return self.send_json_command(command_dict)

    def _read_response(self):
        """Reads and prints all available lines from the Arduino."""

        if self.mock_mode or not self.is_connected():
            return
            
        time.sleep(0.2)
        response_lines = []
        while self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                response_lines.append(line)
        if response_lines:
            print(f"Arduino: {' | '.join(response_lines)}")

    def disconnect(self):
        """Closes the serial connection or simulates it."""
        if self.mock_mode:
            if self._is_mock_connected:
                print("MOCK: Simulating Arduino disconnection...")
                self._is_mock_connected = False
                print("MOCK: Connection closed.")
            return

        if self.is_connected():
            print("Closing Arduino connection...")
            self.ser.close()
            print("Connection closed.")