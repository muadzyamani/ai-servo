# AI-Controlled Servo Motor with RFID Authentication and Interactive LCD

This project demonstrates controlling a servo motor connected to an Arduino UNO using natural language commands, either typed or spoken. The system is secured by an RFID authentication module, requiring an authorized card scan to begin operation. A lightweight AI model running locally via Ollama (e.g., `phi3:mini`) interprets the commands and generates a structured JSON response to control the servo's actions. A 16x2 parallel LCD provides a rich, interactive user experience with real-time feedback on the system's state and actions.

The system now features a full lifecycle: a dynamic welcome screen, a user-initiated authentication stage, visual feedback for authorized and unauthorized scans, multiple modes of interaction, a variety of complex motor sequences, a system reset command, and a graceful shutdown sequence. It also includes robust testing and development modes to run the software without physical hardware.

## Features

*   **RFID Authentication:** The system waits for an authorized RFID card to be scanned before accepting motor commands. (This can be bypassed for testing).
*   **Interactive Startup:** The Arduino runs a welcome sequence, then waits for the user to type `begin` in the terminal to start the authentication process.
*   **Development & Testing Modes:**
    *   **Authentication Bypass:** A simple toggle in `config.py` to skip the RFID scan, allowing for rapid testing of motor commands.
    *   **Hardware Mocking:** Run the entire Python application without a physical Arduino connected. The mock simulates hardware responses, making it ideal for testing the LLM integration and command logic.
    *   **Simulated Auth Scenarios:** When in mock mode with authentication enabled, the system automatically simulates successful and failed RFID scans to test the full authentication logic without hardware.
*   **Visual Access Control:**
    *   **Success:** A successful scan displays an "Authenticated!" message.
    *   **Failure:** An unauthorized scan triggers an "Access Denied!" message on the LCD and a "no" shake from the servo motor.
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
*   **Robust Arduino State Machine:** The Arduino manages its own state (Welcome, Awaiting Auth, Idle, Thinking, etc.), providing clear user feedback without being blocked by long-running actions.
*   **Interactive LCD Feedback:**
    *   **Welcome Sequence:** A multi-message welcome screen cycles on startup.
    *   **Authentication Prompt:** Displays "Please Scan Card".
    *   **Status Display:** Shows current motor angle and system status ("Ready").
    *   **Thinking Animation:** A dynamic "AI Thinking..." animation plays while the LLM processes a request.
    *   **Action Display:** Shows the current action being performed (e.g., "Action: Sweep", "Reps: 2").
    *   **System Reset:** A `reset` command returns the motor to its home position and restarts the welcome sequence.
    *   **Graceful Shutdown:** An `exit` command triggers a shutdown message on the LCD, homes the motor, and turns off the backlight.
*   **Optimized Arduino Code:** Uses C-style strings and the `F()` macro to conserve precious SRAM, preventing memory-related crashes.
*   **Modular Python Code:** The Python logic is organized into separate files for clarity and maintainability (`config`, `arduino`, `llm`, etc.).

## Hardware Requirements

1.  **Arduino UNO** (or compatible board)
2.  **Servo Motor** (e.g., SG90, MG90S)
3.  **16x2 Parallel LCD Display** (HD44780 compatible - **NOT an I2C version**)
4.  **MFRC522 RFID Reader Module** with cards/fobs
5.  **10k Ohm Potentiometer** (for LCD contrast adjustment)
6.  **220 Ohm Resistor** (for LCD backlight current limiting)
7.  **Jumper Wires**
8.  **Breadboard**
9.  **USB Cable**
10. **Microphone** (for voice command mode)

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
        *   `MFRC522` (Install via Library Manager).
        *   `ArduinoJson` (Install via Library Manager).
4.  **Python Libraries:** Listed in `requirements.txt`.
5.  **System Dependencies for PyAudio:**
    *   **Windows/macOS:** Usually works out-of-the-box with `pip`.
    *   **Linux (Debian/Ubuntu):** You may need to install PortAudio development files: `sudo apt-get install portaudio19-dev python3-pyaudio`.

## Setup Instructions

### 1. Hardware Wiring

**(Please refer to a schematic for your specific board if needed. This is a general guide.)**

**A. Servo Motor to Arduino:**
*   **Servo Signal (Orange/Yellow):** Connect to Arduino Digital Pin `9`.
*   **Servo VCC (Red):** Connect to Arduino `5V`.
*   **Servo GND (Brown/Black):** Connect to Arduino `GND`.

**B. MFRC522 RFID Reader to Arduino:**
*   **SDA:** Connect to Arduino Digital Pin `7`.
*   **SCK:** Connect to Arduino Digital Pin `13` (SPI SCK).
*   **MOSI:** Connect to Arduino Digital Pin `11` (SPI MOSI).
*   **MISO:** Connect to Arduino Digital Pin `12` (SPI MISO).
*   **RST:** Connect to Arduino Digital Pin `8`.
*   **GND:** Connect to Arduino `GND`.
*   **3.3V:** Connect to Arduino `3.3V` (**Important: Do not connect to 5V**).

**C. 16x2 Parallel LCD to Arduino:**
*   **LCD VSS (Pin 1):** Connect to Arduino `GND`.
*   **LCD VDD/VCC (Pin 2):** Connect to Arduino `5V`.
*   **LCD VO (Pin 3 - Contrast):** Connect to the middle pin of the 10k Potentiometer.
    *   Connect the other two legs of the potentiometer to Arduino `5V` and `GND`.
*   **LCD RS (Pin 4):** Connect to Arduino Analog Pin `A0`.
*   **LCD R/W (Pin 5):** Connect to Arduino `GND`.
*   **LCD E (Pin 6):** Connect to Arduino Digital Pin `6`.
*   **LCD D4 (Pin 11):** Connect to Arduino Digital Pin `5`.
*   **LCD D5 (Pin 12):** Connect to Arduino Digital Pin `4`.
*   **LCD D6 (Pin 13):** Connect to Arduino Digital Pin `3`.
*   **LCD D7 (Pin 14):** Connect to Arduino Digital Pin `2`.
*   **LCD K / LED- (Pin 16):** Connect to Arduino `GND`.
*   **LCD A / LED+ (Pin 15):** Connect one end of the 220 Ohm resistor to this pin. Connect the other end of the resistor to **Arduino Digital Pin `10`**. (This allows software control of the backlight).

### 2. Software Setup

**A. Clone or Download Project Files:**
   Ensure you have all the project files structured correctly.

**B. Setup Python Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

**C. Install Python Dependencies:**
   With your virtual environment activated, install the dependencies from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

**D. Setup Ollama:**
   1.  Install and run the Ollama application from [ollama.com](https://ollama.com).
   2.  Pull the recommended model: `ollama pull phi3:mini`.
   3.  Verify the model is available by running `ollama list`.

**E. Upload Arduino Sketch:**
   1.  Open `servo_lcd_display.ino` with the Arduino IDE.
   2.  **Install Libraries:** Go to `Tools > Manage Libraries...`. Search for and install `ArduinoJson` by Benoit Blanchon and `MFRC522` by GithubCommunity.
   3.  Go to `Tools > Board` and select your "Arduino UNO".
   4.  Go to `Tools > Port` and select the correct COM port.
   5.  Click the "Upload" button.

### 3. Configuration

**A. Find Your RFID Card's UID:**
   1.  After uploading the Arduino sketch, open the Arduino IDE's **Serial Monitor** (`Tools > Serial Monitor` or `Ctrl+Shift+M`).
   2.  Set the baud rate in the bottom-right corner to **115200**.
   3.  Scan your card. A message like `Card detected for auth! UID:0496C72B` will appear.
   4.  Copy the UID (`0496c72b`). **Close the Serial Monitor** to free the port.

**B. Configure Python (`config.py`):**
*   Open the `config.py` file.
*   **`AUTHORIZED_UIDS`**: Paste your card's UID (in lowercase) into this dictionary.
*   **`SERIAL_PORT`**: Match this to your Arduino's COM port (e.g., `'COM3'` on Windows, `'/dev/ttyACM0'` on Linux).
*   **`OLLAMA_MODEL`**: Set to the Ollama model you are using (e.g., `"phi3:mini"`).

*   **Testing Toggles:**
    *   **`USE_MOCK_ARDUINO`**: Set to `True` to run the script without a physical Arduino. Ideal for testing LLM integration. When `True`, the `SERIAL_PORT` setting is ignored.
    *   **`BYPASS_RFID_AUTH`**: Set to `True` to skip the RFID scan step and go directly to the command prompt. Useful for rapid development.

*   **Application Settings:**
    *   **`AUTHORIZED_UIDS`**: Paste your card's UID (in lowercase) into this dictionary.
    *   **`SERIAL_PORT`**: Match this to your Arduino's COM port (e.g., `'COM3'` on Windows, `'/dev/ttyACM0'` on Linux).
    *   **`OLLAMA_MODEL`**: Set to the Ollama model you are using (e.g., `"phi3:mini"`).

**C. Verify Arduino Pins (`config.h`):**
*   Pin definitions for the LCD, Servo, and RFID reader are in `config.h`. Ensure they match your wiring.

## Running the Project

1.  **Start Ollama:** Make sure the Ollama service is running.
2.  **Connect Arduino:** (Skip if using mock mode). Connect your wired Arduino to the computer via USB. The LCD should light up and begin its welcome sequence.
3.  **Activate Python Environment:** If using a venv, activate it.
4.  **Run the Python Script:**
    ```bash
    python main.py
    ```
5.  **Begin Interaction:**
    The script will connect and show a prompt based on your `config.py` settings. It will clearly indicate if you are in mock mode and if RFID authentication is enabled or disabled.

    **Example (Normal Operation):**
    ```
    -------------------------------------------
    System connected. Arduino is in idle mode.
    RFID Authentication: ENABLED
    Type 'begin' to start authentication.
    -------------------------------------------
    > 
    ```
    **Example (Bypass Enabled):**
    ```
    -------------------------------------------
    System connected. Arduino is in idle mode.
    RFID Authentication: DISABLED (Testing Mode)
    Type 'begin' to start motor control.
    -------------------------------------------
    > 
    ```
    Type `begin` and press Enter. If authentication is enabled, you will be prompted to scan a card. Otherwise, you will proceed directly to the main command prompt.

6.  **Interact via CLI:**
    After successful authentication (or bypass), the main command prompt will appear.
    **Example Commands:**
    *   `set to 45 degrees`
    *   `shake your head no`
    *   `sweep the area`
    *   `speech` - The script will print "Listening..." and you can speak your command.
    *   `help` - Displays a list of available commands and examples.
    *   `reset` - Resets the motor and restarts the welcome screen on the LCD.
    *   `exit` - Initiates the shutdown sequence.

## Troubleshooting

*   **`JSON Parse Error: NoMemory` on LCD / Servo not moving:** This means the Arduino ran out of SRAM. The current code is optimized to prevent this, but if you add more features, ensure you use C-style strings (`const char*`) and the `F()` macro instead of the `String` class for constant text.
*   **`PermissionError` on COM port:** The Arduino IDE's Serial Monitor must be closed. Check that `SERIAL_PORT` in `config.py` is correct.
*   **LCD Not Displaying Anything / All Black Boxes:** **Adjust the 10k potentiometer** for contrast. This is the most common fix. Double-check all wiring.
*   **RFID Reader Not Working:** Ensure it is powered from the **3.3V pin**, not the 5V pin. Double-check all SPI pin connections (SDA, SCK, MOSI, MISO, RST).
*   **Error connecting to Ollama:** Ensure the Ollama application/service is running.
*   **Voice Commands Not Working:** Ensure your microphone is connected and selected as the default input device. Check your internet connection for Google's speech recognition service.
*   **Servo Jittering:** The servo may need a separate, more powerful 5V power supply. Remember to connect the external supply's ground to the Arduino's ground.