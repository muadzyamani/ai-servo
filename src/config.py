# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3:mini"

# --- Authentication ---
# Add your RFID card/fob UIDs here.
# To find your UID, run the Arduino code and scan your card. The UID will
# be printed in the Arduino IDE's Serial Monitor.
# The key is the UID string, the value is a username for display.
AUTHORIZED_UIDS = {
    "0496c72b": "Admin",
    # "29aeaed4": "User1" # Replace with your actual card UID
}

# --- MOCK MODE TOGGLE ---
# Set to True to simulate Arduino connection for testing without hardware.
# Set to False for normal operation with a connected Arduino.
USE_MOCK_ARDUINO = False 

# --- Hardware Settings (ignored if USE_MOCK_ARDUINO is True) ---
SERIAL_PORT = 'COM3'
SERIAL_BAUDRATE = 115200 # Make sure this matches Arduino
MOTOR_MIN_ANGLE = 0
MOTOR_MAX_ANGLE = 180
MOTOR_DEFAULT_STEP = 15
MOTOR_INITIAL_ANGLE = 90