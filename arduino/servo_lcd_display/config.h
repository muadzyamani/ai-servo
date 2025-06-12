#ifndef CONFIG_H
#define CONFIG_H

// --- Standard Arduino & Library Includes ---
#include <Arduino.h> // Good practice to include for types like String, etc.
#include <Servo.h>
#include <LiquidCrystal.h>
#include <ArduinoJson.h>

// --- Servo Configuration ---
extern Servo myservo; // Declare that 'myservo' exists elsewhere
const int servoPin = 9;
const int INITIAL_ANGLE = 90;
extern int currentAngle; // Declare global variable
const int MIN_ANGLE = 0;
const int MAX_ANGLE = 180;

// --- LCD Pin Configuration ---
const int backlightPin = 10;
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
extern LiquidCrystal lcd; // Declare that 'lcd' exists elsewhere

// --- State Management ---
enum DisplayState {
  WELCOME_SEQUENCE,
  IDLE,
  THINKING,
  EXECUTING_ACTION,
  SHUTTING_DOWN
};
extern DisplayState currentDisplayState; // Declare global variable

// --- Timers and Constants for States ---

// Welcome Sequence
const unsigned long welcomeInterval = 3000;
extern unsigned long lastWelcomeTime;
extern int welcomeMessageIndex;
extern String welcomeLines[];
extern const int numWelcomeLines;

// Thinking Animation
const int animationInterval = 350;
extern unsigned long lastAnimationTime;
extern int animationFrame;
extern String thinkingText;
extern String thinkingFrames[];
extern const int numThinkingFrames;

// EXECUTING_ACTION State
extern unsigned long actionDisplayStartTime;
const unsigned long actionDisplayDuration = 3000;

// SHUTTING_DOWN State
extern unsigned long shutdownStartTime;
const unsigned long shutdownDisplayDuration = 3000;

#endif // CONFIG_H