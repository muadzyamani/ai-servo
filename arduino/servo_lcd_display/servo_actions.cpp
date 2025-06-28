#include "servo_actions.h" // Include the header for this implementation
#include "display_functions.h" // We need this to call displayActionStatus

//==============================================================================
// COMMAND EXECUTION FUNCTIONS - Called by the JSON parser
//==============================================================================

void executeGoTo(int angle) {
  angle = constrain(angle, MIN_ANGLE, MAX_ANGLE);
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
    myservo.write(MIN_ANGLE); delay(400);
    myservo.write(MAX_ANGLE); delay(400);
  }
  myservo.write(startAngle);
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
  myservo.write(center); delay(200);
  for (int i = 0; i < times; i++) {
    myservo.write(center - nod_range); delay(300);
    myservo.write(center + nod_range); delay(300);
  }
  myservo.write(center);
  currentAngle = center;
  Serial.println("Nod sequence complete.");
}

void executeShake(int times) {
  displayActionStatus("Action: Shake", "Times: " + String(times));
  Serial.println("Executing chaotic shake sequence...");
  int center = 90;
  int shake_range = 45;
  int shake_movements = times * 6;
  randomSeed(analogRead(A0));
  myservo.write(center); delay(200);
  for (int i = 0; i < shake_movements; i++) {
    int randomAngle = random(center - shake_range, center + shake_range + 1);
    int randomDelay = random(70, 150);
    myservo.write(randomAngle);
    delay(randomDelay);
  }
  myservo.write(center);
  currentAngle = center;
  Serial.println("Shake sequence complete.");
}

/**
 * @brief Performs the shake motion without changing the LCD or system state.
 * This is a "silent" action used for feedback during other states.
 */
void executeShakeSilent(int times) {
  int center = 90;
  int shake_range = 45;
  int shake_movements = times * 6;
  randomSeed(analogRead(A0));
  myservo.write(center); delay(200);
  for (int i = 0; i < shake_movements; i++) {
    int randomAngle = random(center - shake_range, center + shake_range + 1);
    int randomDelay = random(70, 150);
    myservo.write(randomAngle);
    delay(randomDelay);
  }
  myservo.write(center);
  // Note: We do NOT update currentAngle here because the calling
  // function might not want the center angle to be assumed.
}