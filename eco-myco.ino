#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <FirebaseESP32.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <Eco_Myco_Trend_inferencing.h> 

// Kredensial
#define WIFI_SSID "Aim"
#define WIFI_PASSWORD "987657778m"
#define FIREBASE_HOST "eco-myco-41fc4-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_AUTH "4MNFJCFJfgz4O9gNWk6im59VQGr2ZERw4mWCg5Yi"

#define PIN_FAN 26      
#define PIN_ATOM 25      

Adafruit_BME280 bme;
LiquidCrystal_I2C lcd(0x27, 20, 4); 
FirebaseData fbdo;
FirebaseConfig config;
FirebaseAuth auth;
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "id.pool.ntp.org", 25200);

bool isFan = false, isAtom = false;
String labelRealtime = "Normal";

void checkRemoteCommand() {
    if (WiFi.status() == WL_CONNECTED) {
        if (Firebase.getString(fbdo, "/realtime/current/fan")) {
            String f = fbdo.stringData();
            isFan = (f == "ON");
        }
        if (Firebase.getString(fbdo, "/realtime/current/atom")) {
            String a = fbdo.stringData();
            isAtom = (a == "ON");
        }
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(PIN_FAN, OUTPUT); pinMode(PIN_ATOM, OUTPUT);
    digitalWrite(PIN_FAN, HIGH); digitalWrite(PIN_ATOM, HIGH);
    
    lcd.init(); lcd.backlight();
    bme.begin(0x76);
    
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    config.host = FIREBASE_HOST;
    config.signer.tokens.legacy_token = FIREBASE_AUTH;
    Firebase.begin(&config, &auth);
    timeClient.begin();
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) timeClient.update();

    // 1. Baca Sensor (Offline OK)
    float t = bme.readTemperature();
    float h = bme.readHumidity();
    float p = bme.readPressure() / 100.0;

    // 2. Cek Perintah dari AI/Dashboard (Jika Online)
    static unsigned long lastCheck = 0;
    if (millis() - lastCheck > 2000) {
        checkRemoteCommand();
        lastCheck = millis();
    }

    // 3. Eksekusi Hardware
    digitalWrite(PIN_FAN, isFan ? LOW : HIGH);
    digitalWrite(PIN_ATOM, isAtom ? LOW : HIGH);

    // 4. Update LCD (Offline OK)
    lcd.setCursor(0,0); lcd.print("Suhu: "); lcd.print(t); lcd.print(" C");
    lcd.setCursor(0,1); lcd.print("Humb: "); lcd.print(h); lcd.print(" %");

    // 5. Kirim Data (Jika Online)
    static unsigned long lastUpload = 0;
    if (WiFi.status() == WL_CONNECTED && millis() - lastUpload > 5000) {
        FirebaseJson json;
        json.set("t", t); json.set("h", h); json.set("p", p);
        json.set("fan", isFan ? "ON" : "OFF");
        json.set("atom", isAtom ? "ON" : "OFF");
        json.set("time", timeClient.getFormattedTime());
        Firebase.updateNode(fbdo, "/realtime/current", json);
        lastUpload = millis();
    }
}