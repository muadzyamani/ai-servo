#include <Servo.h>
#include <LiquidCrystal.h>

// Servo Configuration
Servo myservo;
const int servoPin = 9;
int currentAngle = 90;

// LCD Pin Configuration
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// Display States
enum DisplayState { IDLE, THINKING, PROCESSING_RESULT };
DisplayState currentDisplayState = IDLE;

// Animation variables for THINKING state
unsigned long lastAnimationTime = 0;
const int animationInterval = 350; // Milliseconds between animation frames
int animationFrame = 0;
String thinkingText = "AI Thinking";
String thinkingFrames[] = {".  ", ".. ", "..."}; // Dots for animation

// Timer for PROCESSING_RESULT state
unsigned long processingDisplayStartTime = 0;
const unsigned long processingDisplayDuration = 2500; // Show result for 2.5 seconds

void setup() {
    Serial.begin(115200); // MATCH PYTHON'S BAUD RATE
    myservo.attach(servoPin);
    myservo.write(currentAngle);

    lcd.begin(16, 2);
    updateLcdIdle(); // Initial display
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
    if (currentDisplayState == THINKING) {
        if (millis() - lastAnimationTime > animationInterval) {
            displayThinking(); // Update animation frame
        }
    } else if (currentDisplayState == PROCESSING_RESULT) {
        if (millis() - processingDisplayStartTime > processingDisplayDuration) {
            displayIdle(); // Revert to idle screen after showing result/error
        }
    }
    // IDLE state is updated when commands are processed or explicitly set.
}

// Renamed from updateLcdIdle to avoid confusion in the loop
void updateLcdIdle() {
    displayIdle(); // Call the function that sets state and prints
}