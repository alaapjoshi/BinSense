
#include <Servo.h>  // Include the Servo library

Servo myservo;  // Create a servo object to control the servo motor

void setup() {
  myservo.attach(8);  // Attaches the servo on pin 9 to the servo object
}

void loop() {
  // Goes from 0 degrees to 180 degrees in steps of 1 degree
  for (int pos = 90; pos <= 180; pos += 1) { 
    myservo.write(pos);  // Tell servo to go to position in variable 'pos'
    delay(15);           // Waits for the servo to reach the position
  }

  // Goes from 180 degrees to 0 degrees
  for (int pos = 180; pos >= 90; pos -= 1) { 
    myservo.write(pos);  // Tell servo to go to position in variable 'pos'
    delay(15);           // Waits for the servo to reach the position
  }
}