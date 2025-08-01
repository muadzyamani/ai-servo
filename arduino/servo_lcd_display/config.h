#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>
#include <Servo.h>
#include <LiquidCrystal.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <MFRC522.h>

// --- Servo Configuration ---
extern Servo myservo;
const int servoPin = 9;
const int INITIAL_ANGLE = 90;
extern int currentAngle;
const int MIN_ANGLE = 0;
const int MAX_ANGLE = 180;

// --- LCD Pin Configuration ---
const int backlightPin = 10;
const int rs = A0, en = 6, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
extern LiquidCrystal lcd;

// --- MFRC522 RFID Pin Configuration ---
const int rfidRstPin = 8;
const int rfidSdaPin = 7;
extern MFRC522 mfrc522;

// --- State Management ---
enum DisplayState {
  WELCOME_SEQUENCE,
  AWAITING_AUTH,
  AUTH_FAILURE,
  IDLE,
  THINKING,
  EXECUTING_ACTION,
  SHUTTING_DOWN,
  RFID_DETECTED
};
extern DisplayState currentDisplayState;

// --- Timers and Constants for States ---

// Welcome Sequence
const unsigned long welcomeInterval = 3000;
extern unsigned long lastWelcomeTime;
extern int welcomeMessageIndex;
// "Before"
// extern String welcomeLines[];
// extern const int numWelcomeLines;
// "After" - Change to const char* and remove numWelcomeLines
extern const char* welcomeLines[];
extern int numWelcomeLines; // Make it a variable, not a const

// Thinking Animation
const int animationInterval = 350;
extern unsigned long lastAnimationTime;
extern int animationFrame;
// "Before"
// extern String thinkingText;
// extern String thinkingFrames[];
// extern const int numThinkingFrames;
// "After" - Change to const char* and remove numThinkingFrames
extern const char* thinkingText;
extern const char* thinkingFrames[];
extern int numThinkingFrames; // Make it a variable, not a const

// EXECUTING_ACTION State
extern unsigned long actionDisplayStartTime;
const unsigned long actionDisplayDuration = 3000;

// SHUTTING_DOWN State
extern unsigned long shutdownStartTime;
const unsigned long shutdownDisplayDuration = 3000;

// RFID_DETECTED State
extern unsigned long rfidDisplayStartTime;
const unsigned long rfidDisplayDuration = 4000;

// AUTH_FAILURE State
extern unsigned long authFailDisplayStartTime;
const unsigned long authFailDisplayDuration = 2500;

#endif // CONFIG_H