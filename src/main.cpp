#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

const char* ssid = "Wokwi-GUEST";
const char* password = "";

WebServer server(80);

const int LED_PIN = 2;
const int PWM_CHAN = 0;

void handleRoot() {
  server.send(200, "text/plain", "ESP32 Running");
}

// PWM control
void handleUpdate() {
  StaticJsonDocument<128> doc;
  deserializeJson(doc, server.arg("plain"));

  int pwm = doc["pwm"] | 0;
  pwm = constrain(pwm, 0, 255);

  ledcWrite(PWM_CHAN, pwm);

  Serial.print("PWM SET → ");
  Serial.println(pwm);

  server.send(200, "application/json", "{\"ok\":true}");
}

// Light simulation using potentiometer
void handleLight() {
  int timeSec = millis() / 1000;

  int lux = (sin(timeSec * 0.1) + 1) * 500;  // smooth wave

  Serial.println(lux);

  server.send(200, "application/json",
              "{\"lux\":" + String(lux) + "}");
}

void setup() {
  Serial.begin(115200);

  ledcSetup(PWM_CHAN, 5000, 8);
  ledcAttachPin(LED_PIN, PWM_CHAN);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(300);

  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/update", HTTP_POST, handleUpdate);
  server.on("/light", handleLight);

  server.begin();
}

void loop() {
  server.handleClient();
}