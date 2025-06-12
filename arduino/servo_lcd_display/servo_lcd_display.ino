#include <Servo.h>
#include <LiquidCrystal.h>
#include <ArduinoJson.h>

// --- Servo Configuration ---
Servo myservo;
const int servoPin = 9;
const int INITIAL_ANGLE = 90;
int currentAngle = INITIAL_ANGLE;
const int MIN_ANGLE = 0;
const int MAX_ANGLE = 180;

// --- LCD Pin Configuration ---
const int backlightPin = 10;
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// --- State Management ---
// The state machine controls what the Arduino is currently focused on.
enum DisplayState {
  WELCOME_SEQUENCE,
  IDLE,
  THINKING,
  EXECUTING_ACTION,
  SHUTTING_DOWN
};
DisplayState currentDisplayState = WELCOME_SEQUENCE;

// --- Timers and Constants for States ---

// Welcome Sequence
const unsigned long welcomeInterval = 3000;
unsigned long lastWelcomeTime = 0;
int welcomeMessageIndex = 0;
String welcomeLines[] = {
    "Hello, User", "I am Phi3:mini", "Welcome!", "Nice to meet you",
    "Ready for your", "command..."};
const int numWelcomeLines = sizeof(welcomeLines) / sizeof(String);

// Thinking Animation
const int animationInterval = 350;
unsigned long lastAnimationTime = 0;
int animationFrame = 0;
String thinkingText = "AI Thinking";
String thinkingFrames[] = {".  ", ".. ", "..."};

// EXECUTING_ACTION State
unsigned long actionDisplayStartTime = 0;
// How long to show an action's status before returning to IDLE
const unsigned long actionDisplayDuration = 3000;

// SHUTTING_DOWN State
unsigned long shutdownStartTime = 0;
const unsigned long shutdownDisplayDuration = 3000;

//==============================================================================
// SETUP - Runs once at the beginning
//==============================================================================
void setup() {
  Serial.begin(115200);
  myservo.attach(servoPin);
  myservo.write(currentAngle);

  pinMode(backlightPin, OUTPUT);
  digitalWrite(backlightPin, HIGH);
  lcd.begin(16, 2);

  // Start the welcome sequence
  displayWelcomeMessage();

  Serial.println("Arduino Ready. JSON Parser Initialized.");
}


//==============================================================================
// DISPLAY HELPER FUNCTIONS - For updating the LCD
//==============================================================================

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

void displayIdle() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Angle: " + String(currentAngle) + " deg");
  lcd.setCursor(0, 1);
  lcd.print("Status: Ready");
  currentDisplayState = IDLE;
}

void displayThinking() {
  lcd.setCursor(0, 0);
  lcd.print(thinkingText);
  lcd.setCursor(thinkingText.length(), 0);
  lcd.print(thinkingFrames[animationFrame]);

  animationFrame = (animationFrame + 1) % (sizeof(thinkingFrames) / sizeof(String));
  lastAnimationTime = millis();
}

// A generic function to show the status of any action
void displayActionStatus(String line1, String line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1.substring(0, 16)); // Truncate to 16 chars
  lcd.setCursor(0, 1);
  lcd.print(line2.substring(0, 16)); // Truncate to 16 chars
  actionDisplayStartTime = millis();
  currentDisplayState = EXECUTING_ACTION;
}


//==============================================================================
// COMMAND EXECUTION FUNCTIONS - Called by the JSON parser
//==============================================================================

void executeGoTo(int angle) {
  angle = constrain(angle, MIN_ANGLE, MAX_ANGLE); // Safety check
  displayActionStatus("Moving to Angle", String(angle) + " deg");
  currentAngle = angle;
  myservo.write(currentAngle);
  Serial.print("Motor moved to: "); Serial.println(currentAngle);
}

void executeSpin(int times) {
  displayActionStatus("Action: Spin", "Times: " + String(times));
  Serial.println("Executing spin sequence...");
  int startAngle = myservo.read();
  for (int i = 0; i < times; i++) {
    myservo.write(MIN_ANGLE);
    delay(400);
    myservo.write(MAX_ANGLE);
    delay(400);
  }
  myservo.write(startAngle); // Return to start
  currentAngle = startAngle;
  Serial.println("Spin sequence complete.");
}

void executeSweep(int repetitions) {
  displayActionStatus("Action: Sweep", "Reps: " + String(repetitions));
  Serial.println("Executing sweep sequence...");
  int startAngle = myservo.read();
  for (int i = 0; i < repetitions; i++) {
    for (int pos = MIN_ANGLE; pos <= MAX_ANGLE; pos += 2) { myservo.write(pos); delay(15); }
    for (int pos = MAX_ANGLE; pos >= MIN_ANGLE; pos -= 2) { myservo.write(pos); delay(15); }
  }
  myservo.write(startAngle);
  currentAngle = startAngle;
  Serial.println("Sweep sequence complete.");
}

void executeNod(int times) {
  displayActionStatus("Action: Nod", "Times: " + String(times));
  Serial.println("Executing nod sequence...");
  int center = 90;
  int nod_range = 30;
  myservo.write(center);
  delay(200);
  for (int i = 0; i < times; i++) {
    myservo.write(center - nod_range); delay(300);
    myservo.write(center + nod_range); delay(300);
  }
  myservo.write(center);
  currentAngle = center; // Final position is the center
  Serial.println("Nod sequence complete.");
}

void executeShake(int times) {
  displayActionStatus("Action: Shake", "Times: " + String(times));
  Serial.println("Executing chaotic shake sequence...");
  
  // Define the center and range for the shake
  int center = 90;
  int shake_range = 45; // A wider range for a more dramatic shake
  int shake_movements = times * 6; // Do more movements for a longer shake

  // A good practice for randomness is to seed it from a noisy, unused pin.
  randomSeed(analogRead(A0));
  
  myservo.write(center);
  delay(200);

  for (int i = 0; i < shake_movements; i++) {
    // 1. Pick a random new angle within the shake range.
    // The +1 is because random(min, max) is exclusive of max.
    int randomAngle = random(center - shake_range, center + shake_range + 1);
    
    // 2. Pick a random, short delay to make the timing uneven.
    int randomDelay = random(70, 150); 
    
    myservo.write(randomAngle);
    delay(randomDelay);
  }
  
  // Always return to a stable, central position after shaking.
  myservo.write(center);
  currentAngle = center;
  Serial.println("Shake sequence complete.");
}


//==============================================================================
// MAIN LOOP - The heart of the program
//==============================================================================
void loop() {

  // --- Part 1: Process Incoming Serial Data ---
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    // First, check for simple, non-JSON control commands
    if (input.equalsIgnoreCase("THINKING_START")) {
      currentDisplayState = THINKING;
      animationFrame = 0; // Reset animation
      lastAnimationTime = millis();
      lcd.clear();
      // First animation frame will be drawn by the state handler below

    } else if (input.equalsIgnoreCase("IDLE_STATE")) {
      displayIdle();

    } else if (input.equalsIgnoreCase("RESET_STATE")) {
      Serial.println("System reset command received.");
      currentAngle = INITIAL_ANGLE;
      myservo.write(currentAngle);
      currentDisplayState = WELCOME_SEQUENCE;
      welcomeMessageIndex = 0;
      displayWelcomeMessage();

    } else if (input.equalsIgnoreCase("SHUTDOWN_CMD")) {
      Serial.println("Shutdown command received.");
      myservo.write(INITIAL_ANGLE); // Return motor to safe position
      currentDisplayState = SHUTTING_DOWN;
      shutdownStartTime = millis();
      lcd.clear();
      lcd.setCursor(0, 0); lcd.print("System");
      lcd.setCursor(0, 1); lcd.print("Shutting Down...");

    } else {
      // If it's not a simple command, try to parse it as JSON
      StaticJsonDocument<256> doc; // Memory for JSON object
      DeserializationError error = deserializeJson(doc, input);

      if (error) {
        Serial.print(F("JSON Parse Error: ")); Serial.println(error.c_str());
        displayActionStatus("JSON Parse Err!", input);
      } else {
        const char* command = doc["command"];
        if (strcmp(command, "GOTO") == 0)       { executeGoTo(doc["angle"]); }
        else if (strcmp(command, "SPIN") == 0)  { executeSpin(doc["times"] | 1); }
        else if (strcmp(command, "SWEEP") == 0) { executeSweep(doc["repetitions"] | 2); }
        else if (strcmp(command, "NOD") == 0)   { executeNod(doc["times"] | 2); }
        else if (strcmp(command, "SHAKE") == 0) { executeShake(doc["times"] | 2); }
        else {
          Serial.print("Unknown JSON command: "); Serial.println(command);
          displayActionStatus("Unknown Command", command);
        }
      }
    }
  }

  // --- Part 2: Handle Display State Updates (The non-blocking state machine) ---
  if (currentDisplayState == WELCOME_SEQUENCE) {
    if (millis() - lastWelcomeTime > welcomeInterval) {
      welcomeMessageIndex = (welcomeMessageIndex + 2);
      if (welcomeMessageIndex >= numWelcomeLines) {
        displayIdle(); // Finished with welcome, move to IDLE
      } else {
        displayWelcomeMessage();
      }
    }
  } else if (currentDisplayState == THINKING) {
    if (millis() - lastAnimationTime > animationInterval) {
      displayThinking(); // Update animation frame
    }
  } else if (currentDisplayState == EXECUTING_ACTION) {
    if (millis() - actionDisplayStartTime > actionDisplayDuration) {
      displayIdle(); // Revert to idle screen after showing action status
    }
  } else if (currentDisplayState == SHUTTING_DOWN) {
    if (millis() - shutdownStartTime > shutdownDisplayDuration) {
      lcd.clear();
      digitalWrite(backlightPin, LOW); // Turn off backlight
      Serial.println("Display off. Halting execution.");
      while (1) {} // Enter an infinite loop to stop all processing
    }
  }
}