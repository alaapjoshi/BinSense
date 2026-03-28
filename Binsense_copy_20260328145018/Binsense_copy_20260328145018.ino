
#include <Servo.h>  

Servo myservo; 

void setup() {
  myservo.attach(8);  
}

void loop() {
  // Goes from 0 degrees to 180 degrees 
  for (int pos = 90; pos <= 180; pos += 1) { 
    myservo.write(pos);  /
    delay(15);           
  }

  // Goes from 180 degrees to 0 degrees
  for (int pos = 180; pos >= 90; pos -= 1) { 
    myservo.write(pos);
    delay(15);           
  }
}