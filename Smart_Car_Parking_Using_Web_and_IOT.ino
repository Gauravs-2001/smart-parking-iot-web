#include <Servo.h>  
Servo myservo;

#include <LiquidCrystal.h>
LiquidCrystal lcd(13, 12, 11, 10, 9, 8);

const int trigger_A = A10, echo_A = A11; // Slot 1
const int trigger_B = 7, echo_B = 6;     // Slot 2
const int trigger_C = 5, echo_C = 4;     // Slot 3
const int trigger_D = A0, echo_D = A1;   // Slot 4

const int trigger_IN = A12, echo_IN = A13;  // IN Sensor (Entry)
const int trigger_OUT = A14, echo_OUT = A15; // OUT Sensor (Exit)

long distance_A, distance_B, distance_C, distance_D, distance_IN, distance_OUT;
int S1 = 0, S2 = 0, S3 = 0, S4 = 0;
int totalSlots = 4;  
int occupiedSlots = 0;

void setup() {
  Serial.begin(9600);
  lcd.begin(16,2);
  myservo.attach(3);
  myservo.write(180); 

  pinMode(trigger_A, OUTPUT);
  pinMode(echo_A, INPUT);
  pinMode(trigger_B, OUTPUT); 
  pinMode(echo_B, INPUT);
  pinMode(trigger_C, OUTPUT);
  pinMode(echo_C, INPUT);
  pinMode(trigger_D, OUTPUT);
  pinMode(echo_D, INPUT);

  pinMode(trigger_IN, OUTPUT);
  pinMode(echo_IN, INPUT);
  pinMode(trigger_OUT, OUTPUT);
  pinMode(echo_OUT, INPUT);

  lcd.setCursor(0, 0);
  lcd.print("  Car Parking  ");
  lcd.setCursor(0, 1);
  lcd.print("    System     ");
  delay(2000);
  lcd.clear();   
}

long check_distance(int triggerPin, int echoPin) {
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);
  return pulseIn(echoPin, HIGH, 30000) / 29 / 2; 
}

void loop() {
  distance_A = check_distance(trigger_A, echo_A);
  distance_B = check_distance(trigger_B, echo_B);
  distance_C = check_distance(trigger_C, echo_C);
  distance_D = check_distance(trigger_D, echo_D);
  distance_IN = check_distance(trigger_IN, echo_IN);
  distance_OUT = check_distance(trigger_OUT, echo_OUT);

  S1 = (distance_A < 10) ? 1 : 0;
  S2 = (distance_B < 10) ? 1 : 0;
  S3 = (distance_C < 10) ? 1 : 0;
  S4 = (distance_D < 10) ? 1 : 0;

  occupiedSlots = S1 + S2 + S3 + S4;
  int availableSlots = totalSlots - occupiedSlots;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("S1  S2  S3  S4");
  lcd.setCursor(0, 1);
  lcd.print(" ");
  lcd.print(S1);
  lcd.print("   ");
  lcd.print(S2);
  lcd.print("   ");
  lcd.print(S3);
  lcd.print("   ");
  lcd.print(S4);

   
  Serial.print(S1);
  Serial.println("!");
  Serial.print(S2);
  Serial.println("@");
  Serial.print(S3);
  Serial.println("#"); 
  Serial.print(S4);
  Serial.println("$");
  
//  Serial.print("Available Slots: ");
//  Serial.println(availableSlots);

  // जब पार्किंग फुल हो और कोई एंट्री करे तो LCD पर "SORRY PARKING FULL" दिखाएं
  if (availableSlots == 0 && distance_IN < 10) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("SORRY");
    lcd.setCursor(0, 1);
    lcd.print("PARKING FULL");
    //Serial.println("SORRY PARKING FULL");
    delay(2000);
  }

  if (distance_IN < 10 && availableSlots > 0) { 
    myservo.write(90);  // Open gate
    //Serial.println("Gate Opened for Entry!");
    delay(3000);
  } else if (distance_OUT < 10) { 
    myservo.write(90);  // Open gate
    //Serial.println("Gate Opened for Exit!");
    delay(3000);
  } else {
    myservo.write(180); 
  }

  delay(1000);
}
