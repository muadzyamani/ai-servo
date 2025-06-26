#include "display_functions.h" // Include the header for this implementation

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

void displayAwaitingAuth() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Please Scan Card");
  lcd.setCursor(0, 1);
  lcd.print("to Authenticate");
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

  animationFrame = (animationFrame + 1) % numThinkingFrames;
  lastAnimationTime = millis();
}

void displayActionStatus(String line1, String line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1.substring(0, 16));
  lcd.setCursor(0, 1);
  lcd.print(line2.substring(0, 16));
  actionDisplayStartTime = millis();
  currentDisplayState = EXECUTING_ACTION;
}