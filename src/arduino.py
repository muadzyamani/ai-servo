import serial
import time
import json

CMD_THINKING_START = "THINKING_START"
CMD_IDLE_STATE = "IDLE_STATE"
CMD_RESET_STATE = "RESET_STATE"
CMD_SHUTDOWN = "SHUTDOWN_CMD"

class ArduinoController:
    """Manages serial communication with the Arduino."""
    def __init__(self, port, baudrate, initial_wait_time=2):
        self.port = port
        self.baudrate = baudrate
        self.initial_wait_time = initial_wait_time
        self.ser = None
    
    def connect(self):
        """Establishes the serial connection to the Arduino."""
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
        while self.ser.in_waiting > 0:
            init_msg = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if init_msg:
                    print(f"Arduino (init): {init_msg}")

    def is_connected(self):
        """Checks if the serial connection is active."""
        return self.ser and self.ser.is_open

    def send_command(self, command_str):
        """Sends a generic, non-angle command string to the Arduino."""
        if not self.is_connected():
            print("Cannot send command: Arduino not connected.")
            return False
        try:
            print(f"Sending control command to Arduino: {command_str}")
            self.ser.write(f"{command_str.strip()}\n".encode('utf-8'))
            time.sleep(0.05)
            self._read_response() # Read any immediate response
            return True
        except serial.SerialException as e:
            print(f"Error writing control command to Arduino: {e}")
            return False

    def send_json_command(self, command_dict):
        """NEW: Serializes a dictionary to a JSON string and sends it."""
        if not self.is_connected():
            print("Cannot send command: Arduino not connected.")
            return False
        try:
            json_string = json.dumps(command_dict)
            print(f"Sending JSON command to Arduino: {json_string}")
            self.ser.write(f"{json_string}\n".encode('utf-8'))
            time.sleep(0.1) # Give Arduino time to start processing
            # We don't wait for the full sequence to finish, just for acknowledgment
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
        time.sleep(0.2)
        response_lines = []
        while self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                response_lines.append(line)
        if response_lines:
            print(f"Arduino: {' | '.join(response_lines)}")

    def disconnect(self):
        """Closes the serial connection."""
        if self.is_connected():
            print("Closing Arduino connection...")
            self.ser.close()
            print("Connection closed.")