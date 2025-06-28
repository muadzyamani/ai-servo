// servo_lcd_display.ino

// Include all our custom header files
#include "config.h"
#include "display_functions.h"
#include "servo_actions.h"
#include "rfid_functions.h"

//==============================================================================
// GLOBAL VARIABLE DEFINITIONS
//==============================================================================

// --- Object Instances ---
Servo myservo;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);
MFRC522 mfrc522(rfidSdaPin, rfidRstPin); 

// --- State Variables ---
DisplayState currentDisplayState = WELCOME_SEQUENCE;
int currentAngle = INITIAL_ANGLE;

// --- Timer Variables ---
unsigned long lastWelcomeTime = 0;
unsigned long lastAnimationTime = 0;
unsigned long actionDisplayStartTime = 0;
unsigned long shutdownStartTime = 0;
unsigned long rfidDisplayStartTime = 0; 
unsigned long authFailDisplayStartTime = 0;

// --- Content/Animation Variables (USING C-STRINGS TO SAVE SRAM) ---
int welcomeMessageIndex = 0;
const char* welcomeLines[] = {
    "Hello, User", "I am Phi3:mini", "Welcome!", "Nice to meet you",
    "Ready for your", "command..."};
// "Before" was in config.h
// "After" - Define the variable here where the array is defined
int numWelcomeLines = sizeof(welcomeLines) / sizeof(const char*);

int animationFrame = 0;
const char* thinkingText = "AI Thinking";
const char* thinkingFrames[] = {".  ", ".. ", "..."};
// "Before" was in config.h
// "After" - Define the variable here where the array is defined
int numThinkingFrames = sizeof(thinkingFrames) / sizeof(const char*);


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

  SPI.begin();
  mfrc522.PCD_Init();
  
  displayWelcomeMessage();

  // Use F() macro to keep strings in Flash memory instead of SRAM
  Serial.println(F("Arduino Ready. To find your card UID for config.py,"));
  Serial.println(F("run main.py and scan your card now."));
}


//==============================================================================
// MAIN LOOP - The heart of the program
//==============================================================================
void loop() {
  if (currentDisplayState == IDLE || currentDisplayState == EXECUTING_ACTION) {
     handleRfid();
  }

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("AWAIT_AUTH_CMD")) {
      currentDisplayState = AWAITING_AUTH;
      displayAwaitingAuth();
    }
    else if (input.equalsIgnoreCase("AUTH_FAIL_CMD")) {
      currentDisplayState = AUTH_FAILURE;
      authFailDisplayStartTime = millis();
      lcd.clear();
      lcd.print(F("Access Denied!"));
      executeShakeSilent(1);
    }
    else if (input.equalsIgnoreCase("AUTH_SUCCESS_CMD")) {
      lcd.clear();
      lcd.print(F("Authenticated!"));
      currentAngle = INITIAL_ANGLE;
      myservo.write(currentAngle);
      delay(2000);
      displayIdle();
    }
    else if (input.equalsIgnoreCase("THINKING_START")) {
      currentDisplayState = THINKING;
      animationFrame = 0;
      lastAnimationTime = millis();
      lcd.clear();
    }
    else if (input.equalsIgnoreCase("IDLE_STATE")) {
      displayIdle();
    }
    else if (input.equalsIgnoreCase("RESET_STATE")) {
      Serial.println(F("System reset command received."));
      currentAngle = INITIAL_ANGLE;
      myservo.write(currentAngle);
      currentDisplayState = WELCOME_SEQUENCE;
      welcomeMessageIndex = 0;
      displayWelcomeMessage();
    }
    else if (input.equalsIgnoreCase("SHUTDOWN_CMD")) {
      Serial.println(F("Shutdown command received."));
      myservo.write(INITIAL_ANGLE);
      currentDisplayState = SHUTTING_DOWN;
      shutdownStartTime = millis();
      lcd.clear();
      lcd.setCursor(0, 0); lcd.print(F("System"));
      lcd.setCursor(0, 1); lcd.print(F("Shutting Down..."));
    }
    else {
      // --- INCREASED JSON DOCUMENT SIZE FOR ROBUSTNESS ---
      StaticJsonDocument<384> doc;
      DeserializationError error = deserializeJson(doc, input);

      if (error) {
        Serial.print(F("JSON Parse Error: ")); Serial.println(error.c_str());
        // "Before" was okay because input was a String
        // "After" - input is a String, which is fine
        displayActionStatus("JSON Parse Err!", input);
      } else {
        const char* command = doc["command"];
        if (strcmp(command, "GOTO") == 0)       { executeGoTo(doc["angle"]); }
        else if (strcmp(command, "SPIN") == 0)  { executeSpin(doc["times"] | 1); }
        else if (strcmp(command, "SWEEP") == 0) { executeSweep(doc["repetitions"] | 2); }
        else if (strcmp(command, "NOD") == 0)   { executeNod(doc["times"] | 2); }
        else if (strcmp(command, "SHAKE") == 0) { executeShake(doc["times"] | 2); }
        else {
          Serial.print(F("Unknown JSON command: ")); Serial.println(command);
          // "Before" command was a const char*
          // "After" - Explicitly cast it to a String for the function
          displayActionStatus("Unknown Command", String(command));
        }
      }
    }
  }

  // --- Part 2: Handle Display State Updates ---
  if (currentDisplayState == AUTH_FAILURE) {
    if (millis() - authFailDisplayStartTime > authFailDisplayDuration) {
      displayAwaitingAuth(); 
      currentDisplayState = AWAITING_AUTH;
    }
  }
  else if (currentDisplayState == AWAITING_AUTH) {
    handleAuthenticationScan();
  }
  else if (currentDisplayState == WELCOME_SEQUENCE) {
    if (millis() - lastWelcomeTime > welcomeInterval) {
      welcomeMessageIndex = (welcomeMessageIndex + 2);
      if (welcomeMessageIndex >= numWelcomeLines) {
        displayIdle();
      } else {
        displayWelcomeMessage();
      }
    }
  }
  else if (currentDisplayState == THINKING) {
    if (millis() - lastAnimationTime > animationInterval) {
      displayThinking();
    }
  }
  else if (currentDisplayState == EXECUTING_ACTION) {
    if (millis() - actionDisplayStartTime > actionDisplayDuration) {
      displayIdle();
    }
  }
  else if (currentDisplayState == RFID_DETECTED) {
    if (millis() - rfidDisplayStartTime > rfidDisplayDuration) {
        displayIdle();
    }
  }
  else if (currentDisplayState == SHUTTING_DOWN) {
    if (millis() - shutdownStartTime > shutdownDisplayDuration) {
      lcd.clear();
      digitalWrite(backlightPin, LOW);
      Serial.println(F("Display off. Halting execution."));
      while (1) {}
    }
  }
}