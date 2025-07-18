import serial
import time
import json
import src.config as cfg

CMD_THINKING_START = "THINKING_START"
CMD_IDLE_STATE = "IDLE_STATE"
CMD_RESET_STATE = "RESET_STATE"
CMD_SHUTDOWN = "SHUTDOWN_CMD"
CMD_AWAIT_AUTH = "AWAIT_AUTH_CMD"
CMD_AUTH_SUCCESS = "AUTH_SUCCESS_CMD"
CMD_AUTH_FAIL = "AUTH_FAIL_CMD"


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
        if not self.is_connected() or self.mock_mode:
            return
        time.sleep(0.1)
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
            # print(f"Sending control command to Arduino: {command_str}") # Less verbose for this one
            self.ser.write(f"{command_str.strip()}\n".encode('utf-8'))
            time.sleep(0.05)
            # No response read here, it's a fire-and-forget command
            return True
        except serial.SerialException as e:
            print(f"Error writing control command to Arduino: {e}")
            return False

    def wait_for_response(self, prefix, timeout=30):
        """
        Waits for a specific response line from the Arduino.
        Returns the data part of the response, or None on timeout.
        
        In mock mode, this method can simulate different RFID scenarios:
        - If BYPASS_RFID_AUTH is True, it returns a valid UID immediately
        - If BYPASS_RFID_AUTH is False, it can simulate various auth scenarios
        """
        if not self.is_connected():
            return None

        if self.mock_mode:
            print("MOCK: Waiting for response...")
            
            # If we're in mock mode but NOT bypassing RFID, simulate the full auth process
            if not cfg.BYPASS_RFID_AUTH and prefix == "Card detected for auth! UID:":
                return self._simulate_rfid_auth_scenarios()
            
            # For non-RFID responses or when bypassing RFID, return success
            time.sleep(1)
            if prefix == "Card detected for auth! UID:":
                # Return a valid UID for successful auth
                mock_uid = next(iter(cfg.AUTHORIZED_UIDS))
                print(f"MOCK Arduino: {prefix}{mock_uid}")
                return mock_uid
            else:
                # For other types of responses, return a generic success
                print(f"MOCK Arduino: {prefix}SUCCESS")
                return "SUCCESS"

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith(prefix):
                    print(f"Arduino response received: {line}")
                    return line[len(prefix):].strip()
            time.sleep(0.1) # Don't spam the CPU
        
        print("Timed out waiting for Arduino response.")
        return None

    def _simulate_rfid_auth_scenarios(self):
        """
        Simulates different RFID authentication scenarios for testing.
        This allows testing the full authentication flow even in mock mode.
        """
        print("MOCK: Simulating RFID card scan scenarios...")
        print("MOCK: Options - (1) Valid card, (2) Invalid card, (3) Timeout")
        print("MOCK: Auto-selecting scenario...")
        
        # You can modify this logic to test different scenarios
        # For now, let's simulate a mix of scenarios
        import random
        scenario = random.choice([1, 1, 1, 2])  # Mostly valid, sometimes invalid
        
        if scenario == 1:
            # Valid card
            time.sleep(2)  # Simulate delay
            mock_uid = next(iter(cfg.AUTHORIZED_UIDS))
            print(f"MOCK Arduino: Card detected for auth! UID:{mock_uid}")
            return mock_uid
        elif scenario == 2:
            # Invalid card
            time.sleep(2)  # Simulate delay
            invalid_uid = "DEADBEEF"  # Not in authorized list
            print(f"MOCK Arduino: Card detected for auth! UID:{invalid_uid}")
            return invalid_uid
        else:
            # Timeout
            time.sleep(5)
            print("MOCK: Simulating timeout (no card scanned)")
            return None

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