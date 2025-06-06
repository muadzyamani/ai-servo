#include <Servo.h>
#include <LiquidCrystal.h>

// Servo Configuration
Servo myservo;
const int servoPin = 9;
const int INITIAL_ANGLE = 90;
int currentAngle = INITIAL_ANGLE;

// LCD Pin Configuration
const int backlightPin = 10;
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// Display States
enum DisplayState { WELCOME_SEQUENCE, IDLE, THINKING, PROCESSING_RESULT, SHUTTING_DOWN };
DisplayState currentDisplayState = WELCOME_SEQUENCE;

// Welcome Sequence Variables
const unsigned long welcomeInterval = 3000;
unsigned long lastWelcomeTime = 0;
int welcomeMessageIndex = 0;
String welcomeLines[] = {
    "Hello, User",
    "I am Phi3:mini",
    "Welcome!",
    "Nice to meet you",
    "Ready for your",
    "command..."
};
const int numWelcomeLines = sizeof(welcomeLines) / sizeof(String);

// Animation variables for THINKING state
unsigned long lastAnimationTime = 0;
const int animationInterval = 350; // Milliseconds between animation frames
int animationFrame = 0;
String thinkingText = "AI Thinking";
String thinkingFrames[] = {".  ", ".. ", "..."}; // Dots for animation

// Timer for PROCESSING_RESULT state
unsigned long processingDisplayStartTime = 0;
const unsigned long processingDisplayDuration = 2500; // Show result for 2.5 seconds

// Timer for SHUTTING_DOWN state
unsigned long shutdownStartTime = 0;
const unsigned long shutdownDisplayDuration = 3000;

// Function to display the current welcome message
void displayWelcomeMessage() {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(welcomeLines[welcomeMessageIndex]);
    
    if (welcomeMessageIndex + 1 < numWelcomeLines) {
        lcd.setCursor(0, 1);
        lcd.print(welcomeLines[welcomeMessageIndex + 1]);
    }
    lastWelcomeTime = millis();
}

void setup() {
    Serial.begin(115200); // MATCH PYTHON'S BAUD RATE
    myservo.attach(servoPin);
    myservo.write(currentAngle);

    pinMode(backlightPin, OUTPUT);
    lcd.begin(16, 2);
    digitalWrite(backlightPin, HIGH);
    displayWelcomeMessage();
    
    Serial.println("Arduino Ready. LCD Initialized. Waiting for command...");
}

void displayIdle() {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Angle: " + String(currentAngle) + " deg");
    lcd.setCursor(0, 1);
    lcd.print("Status: Ready");
    currentDisplayState = IDLE;
}

void displayThinking() {
    lcd.setCursor(0, 0); // Keep "AI Thinking" on first line
    lcd.print(thinkingText);
    lcd.setCursor(thinkingText.length(), 0); // Position after "AI Thinking"
    lcd.print(thinkingFrames[animationFrame]);

    animationFrame = (animationFrame + 1) % (sizeof(thinkingFrames) / sizeof(String));
    lastAnimationTime = millis();
}

void displayProcessing(int target, int actual) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Target: " + String(target));
    lcd.setCursor(0, 1);
    lcd.print("Actual: " + String(actual));
    processingDisplayStartTime = millis();
    currentDisplayState = PROCESSING_RESULT;
}


void loop() {
    // Handle Serial Input
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command.equalsIgnoreCase("THINKING_START")) {
            currentDisplayState = THINKING;
            animationFrame = 0; // Reset animation
            lastAnimationTime = millis(); // Reset timer for first frame
            lcd.clear();
            lcd.setCursor(0,0); // Prepare for thinking text
            // First frame will be drawn by updateLcdThinking below
        } else if (command.equalsIgnoreCase("IDLE_STATE")) {
            displayIdle();
        } else if (command.equalsIgnoreCase("RESET_STATE"))  {
            Serial.println("System reset command received.");
            currentAngle = INITIAL_ANGLE;
            myservo.write(currentAngle);
            currentDisplayState = WELCOME_SEQUENCE;
            welcomeMessageIndex = 0;
            displayWelcomeMessage();
        } else if (command.equalsIgnoreCase("SHUTDOWN_CMD")) {
            Serial.println("Shutdown command received.");
            currentAngle = INITIAL_ANGLE; // Return motor to safe position
            myservo.write(currentAngle);
            currentDisplayState = SHUTTING_DOWN;
            shutdownStartTime = millis(); // Start the shutdown timer
            lcd.clear();
            lcd.setCursor(0, 0); lcd.print("System");
            lcd.setCursor(0, 1); lcd.print("Shutting Down...");
        } else {
            // Assume it's an angle command
            bool isValidNumber = true;
            if (command.length() == 0) isValidNumber = false;
            else {
                for (int i = 0; i < command.length(); i++) {
                    if (i == 0 && command.charAt(i) == '-') continue;
                    if (!isDigit(command.charAt(i))) {
                        isValidNumber = false;
                        break;
                    }
                }
            }

            if (isValidNumber) {
                int targetAngle = command.toInt();
                if (targetAngle >= 0 && targetAngle <= 180) {
                    currentAngle = targetAngle;
                    myservo.write(currentAngle);
                    Serial.print("Motor moved to: "); Serial.println(currentAngle);
                    displayProcessing(targetAngle, myservo.read());
                } else {
                    Serial.print("Invalid angle range: "); Serial.println(command);
                    lcd.clear();
                    lcd.setCursor(0,0); lcd.print("Angle ErrRange!");
                    lcd.setCursor(0,1); lcd.print(command.substring(0,16));
                    processingDisplayStartTime = millis(); // Show error for a bit
                    currentDisplayState = PROCESSING_RESULT; // Use same state to revert to IDLE
                }
            } else {
                Serial.print("Invalid cmd: "); Serial.println(command);
                lcd.clear();
                lcd.setCursor(0,0); lcd.print("Invalid Command!");
                lcd.setCursor(0,1); lcd.print(command.substring(0,16));
                processingDisplayStartTime = millis(); // Show error for a bit
                currentDisplayState = PROCESSING_RESULT; // Use same state to revert to IDLE
            }
        }
    }

    // Handle Display State Updates
    if (currentDisplayState == WELCOME_SEQUENCE) {
        if (millis() - lastWelcomeTime > welcomeInterval) {
            // Move to the next pair of messages
            welcomeMessageIndex = (welcomeMessageIndex + 2) % numWelcomeLines;
            displayWelcomeMessage(); // Show the new message
        }
    } else if (currentDisplayState == THINKING) {
        if (millis() - lastAnimationTime > animationInterval) {
            displayThinking(); // Update animation frame
        }
    } else if (currentDisplayState == PROCESSING_RESULT) {
        if (millis() - processingDisplayStartTime > processingDisplayDuration) {
            displayIdle(); // Revert to idle screen after showing result/error
        }
    }  else if (currentDisplayState == SHUTTING_DOWN) {
        if (millis() - shutdownStartTime > shutdownDisplayDuration) {
            lcd.clear();
            digitalWrite(backlightPin, LOW);
            Serial.println("Display off. Halting execution.");
            // Enter an infinite loop to stop all further processing
            while(1) {}
        }
    }
}