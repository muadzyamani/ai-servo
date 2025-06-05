
# AI-Controlled Servo Motor with LCD Display

This project demonstrates controlling a servo motor connected to an Arduino UNO using natural language commands typed into a CLI. A lightweight AI model running via Ollama (e.g., `phi3:mini`) interprets the commands and determines the servo's target angle. A 16x2 parallel LCD display provides real-time feedback, including the current angle, status, and an "AI Thinking..." animation.

## Features

*   **Natural Language Control:** Send commands like "Open the motor", "Close slightly", "Set to 90 degrees" via a CLI.
*   **AI-Powered Interpretation:** Utilizes a local LLM (via Ollama) to parse commands and determine the desired servo angle.
*   **Keyword Fallback:** For common commands, a faster keyword-based system is used, with LLM as a fallback for more complex queries.
*   **Servo Motor Actuation:** Moves a servo motor to the angle determined by the AI or keywords.
*   **16x2 LCD Feedback:**
    *   Displays current motor angle and system status ("Ready", "AI Thinking...", "Processing").
    *   Shows target and actual angles after a move.
    *   Displays error messages.
    *   Includes a dynamic "AI Thinking..." animation.
*   **Python CLI:** Interactive command-line interface for user input.
*   **Arduino UNO:** Manages the servo and LCD directly.

## Hardware Requirements

1.  **Arduino UNO** (or compatible board)
2.  **Servo Motor** (e.g., SG90, MG90S)
3.  **16x2 Parallel LCD Display** (HD44780 compatible - NOT an I2C version for this setup)
4.  **10k Ohm Potentiometer** (for LCD contrast adjustment)
5.  **220 Ohm Resistor** (or similar, for LCD backlight current limiting - check your LCD datasheet)
6.  **Jumper Wires**
7.  **Breadboard** (recommended)
8.  **USB Cable** (for Arduino programming and communication)

## Software Requirements

1.  **Python 3.7+**
2.  **Ollama:**
    *   Download and install from [ollama.com](https://ollama.com/).
    *   Ensure the Ollama service is running.
    *   Pull an LLM model: `ollama pull phi3:mini` (recommended) or another model of your choice.
3.  **Arduino IDE:**
    *   Download and install from [arduino.cc](https://www.arduino.cc/en/software).
    *   Install the `LiquidCrystal` library (usually comes pre-installed with the IDE).
4.  **Python Libraries:**
    *   `pyserial`
    *   `requests`

## Setup Instructions

### 1. Hardware Wiring

**A. Servo Motor to Arduino:**
*   **Servo Signal (Orange/Yellow wire):** Connect to Arduino Digital Pin `9`.
*   **Servo VCC (Red wire):** Connect to Arduino `5V`.
*   **Servo GND (Brown/Black wire):** Connect to Arduino `GND`.

**B. 16x2 Parallel LCD to Arduino:**
*   **LCD VSS (Pin 1):** Connect to Arduino `GND`.
*   **LCD VDD/VCC (Pin 2):** Connect to Arduino `5V`.
*   **LCD VO (Pin 3 - Contrast):** Connect to the middle wiper of the 10k Potentiometer.
    *   One outer leg of the potentiometer to Arduino `5V`.
    *   The other outer leg of the potentiometer to Arduino `GND`.
*   **LCD RS (Pin 4 - Register Select):** Connect to Arduino Digital Pin `12`.
*   **LCD R/W (Pin 5 - Read/Write):** Connect to Arduino `GND` (we are only writing).
*   **LCD E (Pin 6 - Enable):** Connect to Arduino Digital Pin `11`.
*   **LCD D0-D3 (Pins 7-10):** Not used in 4-bit mode. Leave disconnected.
*   **LCD D4 (Pin 11):** Connect to Arduino Digital Pin `5`.
*   **LCD D5 (Pin 12):** Connect to Arduino Digital Pin `4`.
*   **LCD D6 (Pin 13):** Connect to Arduino Digital Pin `3`.
*   **LCD D7 (Pin 14):** Connect to Arduino Digital Pin `2`.
*   **LCD A / LED+ (Pin 15 - Backlight Anode):** Connect one end of the 220 Ohm resistor to this pin. Connect the other end of the resistor to Arduino `5V`.
*   **LCD K / LED- (Pin 16 - Backlight Cathode):** Connect to Arduino `GND`.

**Important:** Double-check all connections before powering on. Adjust the 10k potentiometer for LCD contrast if nothing appears on the screen.

### 2. Software Setup

**A. Clone or Download Project Files:**
   Ensure you have `main.py` and `servo_lcd_display.ino` in the same project directory.

**B. Setup Python Virtual Environment (Recommended):**
   Open your terminal or command prompt in the project directory.
   ```bash
   python -m venv venv
   ```
   Activate the virtual environment:
   *   **Windows (Command Prompt):** `venv\Scripts\activate`
   *   **Windows (PowerShell):** `venv\Scripts\Activate.ps1` (You might need to run `Set-ExecutionPolicy Unrestricted -Scope Process` first if you encounter issues)
   *   **macOS/Linux:** `source venv/bin/activate`

**C. Install Python Dependencies:**
   Create a `requirements.txt` file in your project directory with the following content:
   ```txt
   pyserial
   requests
   ```
   Then, with your virtual environment activated, install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

**D. Setup Ollama:**
   1.  Install Ollama from [ollama.com](https://ollama.com) if you haven't already.
   2.  Start the Ollama application/service. This typically involves running the Ollama application you installed.
   3.  Pull the desired model. For this project, `phi3:mini` is recommended due to its balance of size and capability:
       ```bash
       ollama pull phi3:mini
       ```
       You can verify the model is available by running `ollama list`.

**E. Upload Arduino Sketch:**
   1.  Open `servo_lcd_display.ino` with the Arduino IDE.
   2.  Select your Arduino board (e.g., "Arduino UNO") from `Tools > Board`.
   3.  Select the correct COM port for your Arduino from `Tools > Port`.
   4.  Click the "Upload" button (right arrow icon).

## Configuration

**Python Script (`main.py`):**
*   **`SERIAL_PORT`**: Ensure this matches the COM port your Arduino is connected to (e.g., `'COM3'` on Windows, `'/dev/ttyUSB0'` or `'/dev/ttyACM0'` on Linux).
*   **`SERIAL_BAUDRATE`**: Should be `115200` to match the Arduino sketch.
*   **`OLLAMA_MODEL`**: Set to the Ollama model you want to use (e.g., `"phi3:mini"`).
*   **`MOTOR_MIN_ANGLE`**, `MOTOR_MAX_ANGLE`**: Define the operational range of your servo (e.g., `0` and `180`).
*   **`MOTOR_DEFAULT_STEP`**: Angle change for "a bit/slightly" commands (e.g., `15`).
*   **`MOTOR_INITIAL_ANGLE`**: The starting angle for the servo (e.g., `90`).

**Arduino Sketch (`servo_lcd_display.ino`):**
*   The baud rate is set with `Serial.begin(115200);`. This must match `SERIAL_BAUDRATE` in `main.py`.
*   Pin definitions for LCD and Servo are at the top of the sketch. They must match your wiring.

## Running the Project

1.  **Ensure Ollama Service is Running:** The Ollama application should be active in your system tray or as a background service.
2.  **Connect Arduino:** Make sure your Arduino is wired correctly and connected to the computer via USB.
3.  **Activate Python Virtual Environment:** If you are using one (recommended):
    *   Windows: `venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`
4.  **Run the Python Script:**
    Navigate to your project directory in the terminal (if not already there) and run:
    ```bash
    python main.py
    ```
5.  **Interact via CLI:**
    The script will attempt to connect to the Arduino and print messages like:
    ```
    Connected to Arduino on COM3
    Arduino (init): Arduino Ready. LCD Initialized. Waiting for command...

    Motor Control CLI. Type 'exit' to quit.
    Current motor angle assumed to be: 90
    You: 
    ```
    You can now type commands.

    **Example Commands:**
    *   `open the motor`
    *   `close it fully`
    *   `open a bit`
    *   `close slightly`
    *   `set to 45 degrees`
    *   `move to 120`
    *   `return to default position` (This command was added to the LLM prompt: `If the user wants to return to the default or initial condition, assume {MOTOR_INITIAL_ANGLE} degrees.`)
    *   `exit` (to close the program)

    Observe the servo motor and the LCD display reacting to your commands. If the LLM is invoked, you'll see the "AI Thinking..." animation on the LCD.

## File Structure

*   **`main.py`**: The Python script that handles user input from the CLI, communicates with the Ollama AI model, and sends commands to the Arduino.
*   **`servo_lcd_display.ino`**: The Arduino sketch that controls the servo motor and the 16x2 LCD, including the "AI Thinking..." animation.
*   **`requirements.txt`**: Lists Python dependencies for easy installation.
*   **`README.md`**: This file.

## Troubleshooting

*   **Python: `PermissionError: [Errno 13] Access is denied:` on COM port:**
    *   Ensure the Arduino IDE's Serial Monitor is closed.
    *   Make sure no other program is using the COM port (e.g., PuTTY, other terminal emulators).
    *   Try unplugging and replugging the Arduino.
    *   Verify the `SERIAL_PORT` in `main.py` is correct (check Device Manager on Windows or `ls /dev/tty*` on Linux/macOS).
*   **LCD Not Displaying Anything / All Black Boxes:**
    *   Check VCC and GND connections to the LCD.
    *   **Crucially, adjust the 10k potentiometer connected to the LCD's VO pin.** This controls the contrast and is the most common issue.
    *   Verify all RS, E, D4-D7 pin connections are secure and correct.
*   **LCD Backlight Not Working:**
    *   Check the 220 Ohm resistor and its connections to LCD A (Anode/LED+) and 5V.
    *   Check LCD K (Cathode/LED-) connection to GND.
*   **Python: Error connecting to Ollama (e.g., `ConnectionRefusedError`):**
    *   Ensure the Ollama application/service is running.
    *   Verify `OLLAMA_API_URL` in `main.py` is correct (default is `http://localhost:11434/api/generate`).
    *   Check your firewall settings if Ollama is running but still inaccessible.
*   **Servo Not Moving or Jittering:**
    *   Check servo VCC (5V) and GND connections.
    *   Ensure the signal wire is correctly connected to Arduino Pin 9.
    *   If jittering, the servo might not be getting enough stable power. For a single SG90, Arduino 5V is usually fine, but with the LCD also drawing power, ensure your USB port can supply enough current. For more demanding servos or multiple components, an external power supply for the servo might be needed (remember to connect grounds).
*   **"AI Thinking..." Animation Stuck or Not Showing / No LCD Updates:**
    *   Check the baud rates in both `main.py` (`SERIAL_BAUDRATE`) and `servo_lcd_display.ino` (`Serial.begin()`). They *must* match (currently set to `115200`).
    *   Ensure the `THINKING_START` and `IDLE_STATE` commands are correctly sent by Python and parsed by Arduino. You can add `Serial.println()` statements in the Arduino code to debug what it's receiving.
    *   Verify all LCD data and control pin wiring. A single loose wire can cause issues.
*   **Ollama Model Not Found:**
    *   Ensure you have pulled the model specified in `OLLAMA_MODEL` (e.g., `ollama pull phi3:mini`). Run `ollama list` to see available models.