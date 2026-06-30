#define TINY_GSM_MODEM_SIM800
#define SerialMon Serial
#define SerialAT Serial2
#define SerialGPS Serial1
#define TINY_GSM_DEBUG SerialMon
#define GSM_PIN ""

#include <Arduino.h>
#include "secrets.h"   // <-- Firebase + GPRS credentials live here 

// Emergency Button Configuration
#define EMERGENCY_BUTTON_PIN 4
bool lastButtonState = LOW;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// UART Pins
#define MODEM_TX 5
#define MODEM_RX 18
#define GPS_TX_PIN 25
#define GPS_RX_PIN 16

#include <TinyGsmClient.h>
#include <FirebaseClient.h>
#include <TinyGPS++.h>

TinyGsm modem(SerialAT);
TinyGsmClient gsm_client1(modem, 0);
TinyGsmClient gsm_client2(modem, 1);
TinyGPSPlus gps;

ESP_SSLClient ssl_client1, ssl_client2;

GSMNetwork gsm_network(&modem, GSM_PIN, APN, GPRS_USER, GPRS_PASS);
UserAuth user_auth(API_KEY, USER_EMAIL, USER_PASSWORD);
FirebaseApp app;

using AsyncClient = AsyncClientClass;
AsyncClient aClient1(ssl_client1, getNetwork(gsm_network)), aClient2(ssl_client2, getNetwork(gsm_network));
RealtimeDatabase Database;

unsigned long ms = 0;

void asyncCB(AsyncResult &aResult);
void printResult(AsyncResult &aResult);

void setup() {
  SerialMon.begin(115200);
  pinMode(EMERGENCY_BUTTON_PIN, INPUT_PULLUP);
  delay(10);

  SerialMon.println("Wait ...");

  SerialGPS.begin(9600, SERIAL_8N1, GPS_TX_PIN, GPS_RX_PIN);
  SerialAT.begin(115200, SERIAL_8N1, MODEM_TX, MODEM_RX);
  delay(3000);

  SerialMon.println("Initializing modem ...");
  modem.restart();

  String modemInfo = modem.getModemInfo();
  SerialMon.print("Modem Info: ");
  SerialMon.println(modemInfo);

  if (GSM_PIN && modem.getSimStatus() != 3) {
    modem.simUnlock(GSM_PIN);
  }

  SerialMon.print("Waiting for network...");
  if (!modem.waitForNetwork()) {
    SerialMon.println(" fail");
    delay(10000);
    return;
  }
  SerialMon.println(" success");

  if (modem.isNetworkConnected()) {
    DBG("Network connected");
  }

  String ccid = modem.getSimCCID();
  DBG("CCID:", ccid);
  delay(100);

  String imei = modem.getIMEI();
  DBG("IMEI:", imei);
  delay(100);

  String imsi = modem.getIMSI();
  DBG("IMSI:", imsi);
  delay(100);

  String cop = modem.getOperator();
  DBG("Operator:", cop);
  delay(100);

  SerialMon.print("Connecting to APN: ");
  SerialMon.print(APN);
  if (!modem.gprsConnect(APN, GPRS_USER, GPRS_PASS)) {
    SerialMon.println(" fail");
    ESP.restart();
  }
  SerialMon.println(" OK");
  delay(100);

  if (modem.isGprsConnected()) {
    SerialMon.println("GPRS connected");
  }
  delay(100);

  IPAddress local = modem.localIP();
  DBG("Local IP:", local);
  delay(100);

  int csq = modem.getSignalQuality();
  DBG("Signal quality:", csq);
  delay(1000);

  Firebase.printf("Firebase Client v%s\n", FIREBASE_CLIENT_VERSION);

  ssl_client1.setInsecure();
  ssl_client1.setDebugLevel(1);
  ssl_client1.setBufferSizes(2048, 1024);
  ssl_client1.setClient(&gsm_client1);

  ssl_client2.setInsecure();
  ssl_client2.setDebugLevel(1);
  ssl_client2.setBufferSizes(2048, 1024);
  ssl_client2.setClient(&gsm_client2);

  Serial.println("Initializing app...");
  initializeApp(aClient1, app, getAuth(user_auth), asyncCB, "authTask");
  app.getApp<RealtimeDatabase>(Database);
  Database.url(DATABASE_URL);
  Database.setSSEFilters("get,put,patch,keep-alive,cancel,auth_revoked");
  Database.get(aClient2, "/value/", asyncCB, true, "streamTask");
}

void loop() {
  app.loop();
  Database.loop();

  // Emergency button handling
  bool buttonState = digitalRead(EMERGENCY_BUTTON_PIN);
  if (buttonState != lastButtonState && millis() - lastDebounceTime > debounceDelay) {
    if (buttonState == HIGH && app.ready()) {
      logEmergencyEvent();
    }
    lastButtonState = buttonState;
    lastDebounceTime = millis();
  }

  // GPS data handling
  if (millis() - ms > 20000 && app.ready()) {
    char lat_str[12];
    char lng_str[12];

    Serial.println("Getting data: ");
    float lat = 0, lng = 0;

    for (int i = 2; i; i--) {
      while (SerialGPS.available() > 0) {
        gps.encode(SerialGPS.read());
      }
      delay(1000);
    }

    if (gps.location.isValid()) {
      lat = gps.location.lat();
      lng = gps.location.lng();

      dtostrf(lat, 8, 6, lat_str);
      dtostrf(lng, 8, 6, lng_str);

      Serial.print("Latitude = ");
      Serial.println(lat_str);
      Serial.print("Longitude= ");
      Serial.println(lng_str);
    } else {
      Serial.println(F("Invalid"));
    }

    ms = millis();

    JsonWriter writer;
    object_t json, obj1, obj2;
    writer.create(obj1, "lat", lat_str);
    writer.create(obj2, "lng", lng_str);
    writer.join(json, 2, obj1, obj2);

    Database.set<object_t>(aClient1, "/bikes/bike_1/location/", json, asyncCB, "setTask");
  }
}

void logEmergencyEvent() {
  JsonWriter writer;
  object_t json, timestampObj;

  // Create a special timestamp object
  writer.create(timestampObj, ".sv", "timestamp");

  // Create main JSON object
  writer.create(json, "emergency", true);
  writer.create(json, "status", "triggered");
  writer.create(json, "timestamp", timestampObj);

  String path = "/bikes/bike_1/emergency_events/" + String(millis());
  Database.set<object_t>(aClient1, path.c_str(), json, asyncCB, "emergencyTask");

  SerialMon.println("Emergency logged with server timestamp!");
}

void asyncCB(AsyncResult &aResult) {
  printResult(aResult);
}

void printResult(AsyncResult &aResult) {
  if (aResult.isEvent()) {
    Firebase.printf("Event task: %s, msg: %s, code: %d\n", aResult.uid().c_str(), aResult.appEvent().message().c_str(), aResult.appEvent().code());
  }

  if (aResult.isDebug()) {
    Firebase.printf("Debug task: %s, msg: %s\n", aResult.uid().c_str(), aResult.debug().c_str());
  }

  if (aResult.isError()) {
    Firebase.printf("Error task: %s, msg: %s, code: %d\n", aResult.uid().c_str(), aResult.error().message().c_str(), aResult.error().code());
  }

  if (aResult.available()) {
    RealtimeDatabaseResult &RTDB = aResult.to<RealtimeDatabaseResult>();
    if (RTDB.isStream()) {
      Serial.println("----------------------------");
      Firebase.printf("task: %s\n", aResult.uid().c_str());
      Firebase.printf("event: %s\n", RTDB.event().c_str());
      Firebase.printf("path: %s\n", RTDB.dataPath().c_str());
      Firebase.printf("data: %s\n", RTDB.to<const char *>());
      Firebase.printf("type: %d\n", RTDB.type());
    } else {
      Serial.println("----------------------------");
      Firebase.printf("task: %s, payload: %s\n", aResult.uid().c_str(), aResult.c_str());
    }
    Firebase.printf("Free Heap: %d\n", ESP.getFreeHeap());
  }
}
