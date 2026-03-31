#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

WebServer server(80);
const int ledPin = 2; // LED connected to GPIO 2

void handleUpdate() {
  if (server.hasArg("plain")) {
    StaticJsonDocument<200> doc;
    deserializeJson(doc, server.arg("plain"));
    
    int pwmValue = doc["pwm"]; 
    analogWrite(ledPin, pwmValue); // Apply ML prediction to LED
    
    server.send(200, "text/plain", "Sync Successful");
    Serial.print("Applied PWM: ");
    Serial.println(pwmValue);
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin("Wokwi-GUEST", ""); // Special virtual network for Wokwi
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  server.on("/update", HTTP_POST, handleUpdate);
  server.begin();
  Serial.println("\nReady! IP Address: " + WiFi.localIP().toString());
}

void loop() {
  server.handleClient();
}