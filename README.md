# AI-Controlled Servo Motor with Interactive LCD

This project demonstrates controlling a servo motor connected to an Arduino UNO using natural language commands, either typed or spoken. A lightweight AI model running locally via Ollama (e.g., `phi3:mini`) interprets the commands and generates a structured JSON response to control the servo's actions. A 16x2 parallel LCD provides a rich, interactive user experience with real-time feedback on the system's state and actions.

The system now features a full lifecycle: a dynamic welcome screen on startup, multiple modes of interaction, a variety of complex motor sequences, a system reset command, and a graceful shutdown sequence.

## Features

*   **Natural Language Control:** Send commands like "turn a little to the right", "nod your head twice", or "set to 90 degrees".
*   **Voice Command Mode:** Activate speech recognition to control the servo with your voice.
*   **AI-Powered JSON Generation:** Utilizes a local LLM (via Ollama) to parse natural language into a structured JSON command protocol, enabling more complex and reliable actions.
*   **Expanded Command Set:**
    *   **GOTO:** Move to an absolute angle.
    *   **ADJUST:** Move by a relative number of degrees (handled in Python).
    *   **SPIN:** Perform rapid back-and-forth full-range rotations.
    *   **SWEEP:** Smoothly scan back and forth like a radar.
    *   **NOD:** Perform a "yes" motion.
    *   **SHAKE:** Perform a chaotic, random "no" motion.
*   **Robust Arduino State Machine:** The Arduino manages its own state, providing clear user feedback without being blocked by long-running actions.
*   **Interactive LCD Feedback:**
    *   **Welcome Sequence:** A multi-message welcome screen cycles on startup.
    *   **Status Display:** Shows current motor angle and system status ("Ready").
    *   **Thinking Animation:** A dynamic "AI Thinking..." animation plays while the LLM processes a request.
    *   **Action Display:** Shows the current action being performed (e.g., "Action: Sweep", "Reps: 2").
    *   **System Reset:** A `reset` command returns the motor to its home position and restarts the welcome sequence.
    *   **Graceful Shutdown:** An `exit` command triggers a shutdown message on the LCD, homes the motor, and turns off the backlight.
*   **Modular Python Code:** The Python logic is organized into separate files for clarity and maintainability (`config`, `arduino`, `llm`, etc.).
*   **Arduino UNO:** Manages the servo, LCD, and all display states directly, parsing JSON commands received over serial.

## Hardware Requirements

1.  **Arduino UNO** (or compatible board)
2.  **Servo Motor** (e.g., SG90, MG90S)
3.  **16x2 Parallel LCD Display** (HD44780 compatible - **NOT an I2C version**)
4.  **10k Ohm Potentiometer** (for LCD contrast adjustment)
5.  **220 Ohm Resistor** (for LCD backlight current limiting)
6.  **Jumper Wires**
7.  **Breadboard**
8.  **USB Cable**
9.  **Microphone** (for voice command mode)

## Software Requirements

1.  **Python 3.7+**
2.  **Ollama:**
    *   Download and install from [ollama.com](https://ollama.com/).
    *   Ensure the Ollama service is running.
    *   Pull an LLM model: `ollama pull phi3:mini` (recommended).
3.  **Arduino IDE:**
    *   Download from [arduino.cc](https://www.arduino.cc/en/software).
    *   **Required Libraries:**
        *   `LiquidCrystal` (usually pre-installed).
        *   `Servo` (usually pre-installed).
        *   `ArduinoJson` (Must be installed via the Library Manager).
4.  **Python Libraries:** Listed in `requirements.txt`.
5.  **System Dependencies for PyAudio:**
    *   **Windows/macOS:** Usually works out-of-the-box with `pip`.
    *   **Linux (Debian/Ubuntu):** You may need to install PortAudio development files: `sudo apt-get install portaudio19-dev python3-pyaudio`.

## Setup Instructions

### 1. Hardware Wiring

**A. Servo Motor to Arduino:**
*   **Servo Signal (Orange/Yellow):** Connect to Arduino Digital Pin `9`.
*   **Servo VCC (Red):** Connect to Arduino `5V`.
*   **Servo GND (Brown/Black):** Connect to Arduino `GND`.

**B. 16x2 Parallel LCD to Arduino:**
*   **LCD VSS (Pin 1):** Connect to Arduino `GND`.
*   **LCD VDD/VCC (Pin 2):** Connect to Arduino `5V`.
*   **LCD VO (Pin 3 - Contrast):** Connect to the middle pin of the 10k Potentiometer.
    *   Connect the other two legs of the potentiometer to Arduino `5V` and `GND`.
*   **LCD RS (Pin 4):** Connect to Arduino Digital Pin `12`.
*   **LCD R/W (Pin 5):** Connect to Arduino `GND`.
*   **LCD E (Pin 6):** Connect to Arduino Digital Pin `11`.
*   **LCD D0-D3 (Pins 7-10):** Leave disconnected.
*   **LCD D4 (Pin 11):** Connect to Arduino Digital Pin `5`.
*   **LCD D5 (Pin 12):** Connect to Arduino Digital Pin `4`.
*   **LCD D6 (Pin 13):** Connect to Arduino Digital Pin `3`.
*   **LCD D7 (Pin 14):** Connect to Arduino Digital Pin `2`.
*   **LCD K / LED- (Pin 16 - Backlight Cathode):** Connect to Arduino `GND`.
*   **IMPORTANT WIRING CHANGE:**
    *   **LCD A / LED+ (Pin 15 - Backlight Anode):** Connect one end of the 220 Ohm resistor to this pin. Connect the other end of the resistor to **Arduino Digital Pin `10`**. (This allows software control of the backlight).

### 2. Software Setup

**A. Clone or Download Project Files:**
   Ensure you have all the project files in the same directory:
   *   `main.py`
   *   `arduino.py`
   *   `config.py`
   *   `llm.py`
   *   `voice.py`
   *   `servo_lcd_display.ino`
   *   `requirements.txt`

**B. Setup Python Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

**C. Install Python Dependencies:**
   Create a `requirements.txt` file in your project directory with the following content:
   ```txt
   pyserial
   requests
   SpeechRecognition
   PyAudio
   ```
   Then, with your virtual environment activated, install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

**D. Setup Ollama:**
   1.  Install and run the Ollama application from [ollama.com](https://ollama.com).
   2.  Pull the recommended model: `ollama pull phi3:mini`.
   3.  Verify the model is available by running `ollama list`.

**E. Upload Arduino Sketch:**
   1.  Open `servo_lcd_display.ino` with the Arduino IDE.
   2.  **Install Library:** Go to `Tools > Manage Libraries...`. Search for `ArduinoJson` and install the library by Benoit Blanchon.
   3.  Go to `Tools > Board` and select your "Arduino UNO".
   4.  Go to `Tools > Port` and select the correct COM port.
   5.  Click the "Upload" button.

## Configuration

**Python Script (`config.py`):**
*   Open the `config.py` file to adjust settings.
*   **`SERIAL_PORT`**: Match this to your Arduino's COM port (e.g., `'COM3'` on Windows, `'/dev/ttyACM0'` on Linux).
*   **`OLLAMA_MODEL`**: Set to the Ollama model you are using (e.g., `"phi3:mini"`).
*   Other motor parameters (`MOTOR_MIN_ANGLE`, `MOTOR_INITIAL_ANGLE`, etc.) can be adjusted as needed.

**Arduino Sketch (`servo_lcd_display.ino`):**
*   Pin definitions for the LCD, Servo, and **`backlightPin`** are at the top. Ensure they match your wiring.
*   The baud rate `Serial.begin(115200);` must match `SERIAL_BAUDRATE` in `config.py`.

## Running the Project

1.  **Start Ollama:** Make sure the Ollama service is running.
2.  **Connect Arduino:** Connect your wired Arduino to the computer via USB. The LCD should light up and begin the welcome sequence.
3.  **Activate Python Environment:** If using a venv, activate it.
4.  **Run the Python Script:**
    ```bash
    python main.py
    ```
5.  **Interact via CLI:**
    The script will connect and show the prompt:
    ```
    Motor Control CLI. Type 'speech' for voice, 'reset' for default, or 'exit' to quit.
    Current motor angle assumed to be: 90
    You: 
    ```
    **Example Commands:**
    *   `set to 45 degrees`
    *   `turn a little to the right`
    *   `shake your head no`
    *   `nod yes a few times`
    *   `spin around 3 times`
    *   `sweep the area`
    *   `speech` - The script will print "Listening..." and you can speak your command.
    *   `reset` - Resets the motor and restarts the welcome screen on the LCD.
    *   `exit` - Initiates the shutdown sequence on the Arduino and closes the program.

## Troubleshooting

*   **`PermissionError` on COM port:** The Arduino IDE's Serial Monitor must be closed. Check that `SERIAL_PORT` in `config.py` is correct.
*   **LCD Not Displaying Anything / All Black Boxes:** **Adjust the 10k potentiometer** for contrast. This is the most common fix. Double-check all wiring.
*   **LCD Backlight Not Working:** Verify the resistor connection between LCD Pin 15 (A) and Arduino Pin 10. Check that LCD Pin 16 (K) is connected to GND.
*   **`JSON Parse Err!` on LCD:** This means the Arduino received a string that it couldn't parse as a valid JSON command. This can happen if the LLM's response is malformed. Check the console output from `main.py` to see the "LLM Raw Response". You may need to adjust the prompt in `llm.py`.
*   **Error connecting to Ollama:** Ensure the Ollama application/service is running.
*   **Voice Commands Not Working:**
    *   Make sure your microphone is connected and selected as the default input device in your OS.
    *   If you get `PyAudio` errors during installation, you may need to install system libraries (see Software Requirements) or find a pre-compiled wheel for your Python version and OS.
    *   An `sr.RequestError` means the script could not reach Google's speech recognition service; check your internet connection.
*   **Servo Not Moving or Jittering:** Check all power and signal connections. If jittering persists, the servo may need a separate, more powerful 5V power supply (remember to connect its ground to the Arduino's ground).