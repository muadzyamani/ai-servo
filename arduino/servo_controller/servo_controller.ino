#include <Servo.h>

Servo myservo;

const int servoPin = 9;
int currentAngle = 90;

void setup() {
  Serial.begin(9600);
  myservo.attach(servoPin);
  myservo.write(currentAngle);

  Serial.println("Arduino Ready. Waiting for angle...");
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command .trim(); // Remove any leading/trailing whitespace

    int targetAngle = command.toInt();

    // Validate and constrain the angle
    if (targetAngle >= 0 && targetAngle <= 180) {
      currentAngle = targetAngle;
      myservo.write(currentAngle);

      Serial.print("Motor moved to: ");
      Serial.println(currentAngle);
    } else {
      Serial.print("Invalid angle received: ");
      Serial.println(command);
    }
  }
}
