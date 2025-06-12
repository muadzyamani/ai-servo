// Include all our custom header files
#include "config.h"
#include "display_functions.h"
#include "servo_actions.h"

//==============================================================================
// GLOBAL VARIABLE DEFINITIONS
// This is where the variables declared as "extern" in config.h actually live.
//==============================================================================

// --- Object Instances ---
Servo myservo;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// --- State Variables ---
DisplayState currentDisplayState = WELCOME_SEQUENCE;
int currentAngle = INITIAL_ANGLE;

// --- Timer Variables ---
unsigned long lastWelcomeTime = 0;
unsigned long lastAnimationTime = 0;
unsigned long actionDisplayStartTime = 0;
unsigned long shutdownStartTime = 0;

// --- Content/Animation Variables ---
int welcomeMessageIndex = 0;
String welcomeLines[] = {
    "Hello, User", "I am Phi3:mini", "Welcome!", "Nice to meet you",
    "Ready for your", "command..."};
const int numWelcomeLines = sizeof(welcomeLines) / sizeof(String);

int animationFrame = 0;
String thinkingText = "AI Thinking";
String thinkingFrames[] = {".  ", ".. ", "..."};
const int numThinkingFrames = sizeof(thinkingFrames) / sizeof(String);


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

  displayWelcomeMessage(); // Function is now in display_functions.cpp

  Serial.println("Arduino Ready. JSON Parser Initialized.");
}


//==============================================================================
// MAIN LOOP - The heart of the program
//==============================================================================
void loop() {
  // --- Part 1: Process Incoming Serial Data ---
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("THINKING_START")) {
      currentDisplayState = THINKING;
      animationFrame = 0;
      lastAnimationTime = millis();
      lcd.clear();
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
      myservo.write(INITIAL_ANGLE);
      currentDisplayState = SHUTTING_DOWN;
      shutdownStartTime = millis();
      lcd.clear();
      lcd.setCursor(0, 0); lcd.print("System");
      lcd.setCursor(0, 1); lcd.print("Shutting Down...");
    } else {
      StaticJsonDocument<256> doc;
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

  // --- Part 2: Handle Display State Updates ---
  if (currentDisplayState == WELCOME_SEQUENCE) {
    if (millis() - lastWelcomeTime > welcomeInterval) {
      welcomeMessageIndex = (welcomeMessageIndex + 2);
      if (welcomeMessageIndex >= numWelcomeLines) {
        displayIdle();
      } else {
        displayWelcomeMessage();
      }
    }
  } else if (currentDisplayState == THINKING) {
    if (millis() - lastAnimationTime > animationInterval) {
      displayThinking();
    }
  } else if (currentDisplayState == EXECUTING_ACTION) {
    if (millis() - actionDisplayStartTime > actionDisplayDuration) {
      displayIdle();
    }
  } else if (currentDisplayState == SHUTTING_DOWN) {
    if (millis() - shutdownStartTime > shutdownDisplayDuration) {
      lcd.clear();
      digitalWrite(backlightPin, LOW);
      Serial.println("Display off. Halting execution.");
      while (1) {}
    }
  }
}