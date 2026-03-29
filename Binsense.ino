#include <Servo.h>

Servo servo1;  // trash
Servo servo2;  // recycle

// LED pins
const int redLED = 12;
const int greenLED = 7;

// Cooldown system
unsigned long lastActionTime = 0;
const unsigned long cooldown = 5000; // 5 seconds

void setup() {
  Serial.begin(9600);

  servo1.attach(8);
  servo2.attach(11);

  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);

  // Starting positions
  servo1.write(180);  // closed trash
  servo2.write(0);   // closed recycle (IMPORTANT FIX)

  digitalWrite(redLED, LOW);
  digitalWrite(greenLED, LOW);
}

void loop() {

  // Only run if:
  // 1. Data is available
  // 2. Cooldown passed
  if (Serial.available() > 0 && millis() - lastActionTime > cooldown) {
    char incomingByte = Serial.read();
    Serial.println(incomingByte); // DEBUG

    // =========================
    // TRASH
    // =========================
    if (incomingByte == '0') {

      lastActionTime = millis();  // start cooldown

      digitalWrite(redLED, HIGH);
      digitalWrite(greenLED, LOW);

      // Open trash
      for (int pos = 180; pos >= 90; pos--) {
        servo1.write(pos);
        delay(15);
      }

      delay(3000);

      // Close trash
      for (int pos = 90; pos <= 180; pos++) {
        servo1.write(pos);
        delay(15);
      }

      digitalWrite(redLED, LOW);
    }

    // =========================
    // RECYCLE
    // =========================
    else if (incomingByte == '1') {

      lastActionTime = millis();  // start cooldown

      digitalWrite(greenLED, HIGH);
      digitalWrite(redLED, LOW);

      // Open recycle
      for (int pos = 0; pos <= 90; pos++) {
        servo2.write(pos);
        delay(15);
      }

      delay(3000);

      for (int pos = 90; pos >= 0; pos--) {
        servo2.write(pos);
        delay(15);
      }

      digitalWrite(greenLED, LOW);
    }

    else {
      Serial.println("Invalid input");
    }
  }
}
