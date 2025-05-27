#include <WiFi.h>
#include <Firebase_ESP_Client.h>

// 🔹 WiFi Credentials
const char *ssid = "Airtel_CEL9766";
const char *password = "Celab@9766";

// 🔹 Firebase Credentials (अपना सही API Key और URL डालें)
#define API_KEY "AIzaSyCnMd0lVZof14FcoGeoIlnhXAPlRYGIAfU"  // ✅ Firebase API Key
#define DATABASE_URL "https://smart-car-parking-f5696-default-rtdb.firebaseio.com/"  // ✅ Firebase Realtime Database URL

// 🔹 Authentication (Firebase Authentication के लिए)
#define USER_EMAIL "shardamca10@gmail.com"
#define USER_PASSWORD "sharda@1234"

// 🔹 Firebase Objects
FirebaseData firebaseData;
FirebaseAuth auth;
FirebaseConfig config;

// 🔹 Slot Data Variables
String S1 = "0", S2 = "0", S3 = "0", S4 = "0";
char inData[20];
int inDataCount = 0;

void setup() {
  Serial.begin(9600);
  pinMode(2, OUTPUT);  // LED Pin

  // 🔹 WiFi Connect करें
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi Connected!");

  // 🔹 Firebase Configuration सेट करें
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  
  auth.user.email = USER_EMAIL;
  auth.user.password = USER_PASSWORD;
  
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println("✅ Firebase Initialized!");
}

void loop() {
  if (Serial.available()) {
    while (Serial.available()) {
      char receivedChar = Serial.read();

      if (receivedChar == '!') {
        inData[inDataCount] = '\0';  
        S1 = String(inData);
        inDataCount = 0;
      } 
      else if (receivedChar == '@') {
        inData[inDataCount] = '\0';  
        S2 = String(inData);
        inDataCount = 0;
      }
      else if (receivedChar == '#') {
        inData[inDataCount] = '\0';  
        S3 = String(inData);
        inDataCount = 0;
      }
      else if (receivedChar == '$') {
        inData[inDataCount] = '\0';  
        S4 = String(inData);
        inDataCount = 0;
      }
      else {
        inData[inDataCount++] = receivedChar;  
      }
    }

    Serial.println("✅ Updated Data:");
    Serial.print("Slot1: "); Serial.println(S1);
    Serial.print("Slot2: "); Serial.println(S2);
    Serial.print("Slot3: "); Serial.println(S3);
    Serial.print("Slot4: "); Serial.println(S4);
    Serial.println("--------------------------");

    digitalWrite(2, HIGH);
    delay(500);  
    digitalWrite(2, LOW);
  }

  // 🔹 Firebase में JSON Format में डेटा भेजें (सारे स्लॉट एक साथ अपडेट होंगे)
  FirebaseJson json;
  json.set("S1", S1);
  json.set("S2", S2);
  json.set("S3", S3);
  json.set("S4", S4);

  if (Firebase.RTDB.setJSON(&firebaseData, "/Parking", &json)) {
    Serial.println("✅ Data Successfully Updated in Firebase!");
  } else {
    Serial.println("❌ Error: " + firebaseData.errorReason());
  }

  Serial.println("--------------------------");

  delay(1000);  // हर 2 सेकंड में डेटा अपडेट होगा
}
