#include <Servo.h>

Servo myservo;  // create servo object to control a servo
// twelve servo objects can be created on most boards

int pos = 0;    // variable to store the servo position
char inByte = ' ';

void setup() {
  Serial.begin(9600); // set the baud rate
  myservo.attach(A0);  // attaches the servo on pin 9 to the servo object
}

void loop() {

  for (pos = 1; pos >= 1; pos -= 1) { // goes from 180 degrees to 0 degrees
      myservo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(10);                       // waits 15ms for the servo to reach the position
    }
    
  char inByte = Serial.read(); // read the incoming data

  if(inByte == '$') {

    // If the desired byte is read, empty the serial buffer
    while(Serial.available()){
      Serial.read();
      delay(1);
    }

    inByte = "";
    
    for (pos = 1; pos <= 47; pos += 1) { // goes from 0 degrees to 30 degrees
      // in steps of 1 degree
      myservo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(1);                       // waits 15ms for the servo to reach the position
    }
    delay(2000);
    for (pos = 47; pos >= 1; pos -= 1) { // goes from 180 degrees to 30 degrees
      myservo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(1);                       // waits 15ms for the servo to reach the position
    }
    delay(1000);

   }
}
