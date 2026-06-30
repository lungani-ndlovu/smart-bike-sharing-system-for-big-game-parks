#include <WiFi.h>
#include <Firebase_ESP_Client.h>
#include <addons/TokenHelper.h>
#include <addons/RTDBHelper.h>
#include "secrets.h"   

// Pin definitions
#define LED_GREEN 19    // Unlocked indicator
#define LED_RED 21      // Locked indicator
#define RELAY_PIN 18    // Controls relay (solenoid)
#define BUTTON_PIN 23   // Pushbutton to lock (connect to GND when pressed)

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

String firebasePath = "/bikes/bike_1/Lockstatus";
String lastKnownStatus = "locked";
bool isFirebaseReady = false;

unsigned long lastCheck = 0;
const unsigned long checkInterval = 3000;

bool isUnlocked = false;
unsigned long unlockTime = 0;
const unsigned long autoLockDelay = 600000; // 10 minutes

// Button debouncing variables
int buttonState;
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

void setup() {
  Serial.begin(115200);

  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP); // Button with internal pull-up

  digitalWrite(RELAY_PIN, LOW); // Start with relay OFF (solenoid locked)
  setLockedState(true);         // Initialize as locked

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();
  Serial.print("Connected to WiFi. IP: ");
  Serial.println(WiFi.localIP());

  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  auth.user.email = USER_EMAIL;
  auth.user.password = USER_PASSWORD;
  config.token_status_callback = tokenStatusCallback;

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println("Setup complete. Waiting for Firebase updates.");
}

void loop() {
  if (Firebase.ready() && auth.token.uid != "") {
    if (!isFirebaseReady) {
      isFirebaseReady = true;
      Serial.println("Firebase is ready.");
    }

    if (millis() - lastCheck > checkInterval) {
      lastCheck = millis();

      if (Firebase.RTDB.getString(&fbdo, firebasePath)) {
        String status = fbdo.to<String>();

        if (status != lastKnownStatus && (status == "locked" || status == "unlocked")) {
          Serial.print("Lockstatus changed from ");
          Serial.print(lastKnownStatus);
          Serial.print(" to ");
          Serial.println(status);

          lastKnownStatus = status;
          bool locked = (status == "locked");
          setLockedState(locked);

          if (!locked) {
            unlockTime = millis(); // Start auto-lock timer
            isUnlocked = true;
          } else {
            isUnlocked = false;
          }
        }
      } else {
        Serial.print("Firebase read failed: ");
        Serial.println(fbdo.errorReason());
      }
    }
  }

  // Handle button press with debouncing
  int reading = digitalRead(BUTTON_PIN);

  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;

      if (buttonState == LOW && isUnlocked) { // Button pressed and lock is unlocked
        Serial.println("Manual lock button pressed. Locking...");
        Firebase.RTDB.setString(&fbdo, firebasePath, "locked");
        isUnlocked = false;
      }
    }
  }

  lastButtonState = reading;

  // Auto-lock after delay (kept as backup)
  if (isUnlocked && millis() - unlockTime >= autoLockDelay) {
    Serial.println("Auto-lock timeout reached. Locking...");
    Firebase.RTDB.setString(&fbdo, firebasePath, "locked");
    isUnlocked = false;
  }
}

void setLockedState(bool locked) {
  digitalWrite(LED_RED, locked ? HIGH : LOW);
  digitalWrite(LED_GREEN, locked ? LOW : HIGH);

  // Relay logic:
  // HIGH = Relay ON  -> Solenoid energized (UNLOCKED)
  // LOW  = Relay OFF -> Solenoid de-energized (LOCKED)
  digitalWrite(RELAY_PIN, locked ? LOW : HIGH);

  Serial.println(locked ? "LOCKED (Relay OFF)" : "UNLOCKED (Relay ON)");
}
