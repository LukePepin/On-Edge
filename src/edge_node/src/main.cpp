#include <Arduino.h>

#define LED_PIN 13

unsigned long last_heartbeat = 0;
int counter = 0;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  
  // Initialize Serial for ROS 2 Python bridge
  Serial.begin(115200);
  
  // Wait for Serial to initialize (optional, prevents missed messages on startup)
  // while (!Serial);
  
  delay(2000);
}

void loop() {
  unsigned long current_time = millis();
  
  // Publish a heartbeat every 1000ms
  if (current_time - last_heartbeat >= 1000) {
    last_heartbeat = current_time;
    
    // Send raw JSON over Serial. The Raspberry Pi will read this and publish to ROS 2.
    Serial.print("{\"topic\": \"heartbeat\", \"data\": ");
    Serial.print(counter);
    Serial.println("}");
    
    counter++;
    
    // Toggle LED to show activity
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
  
  // ZKP algorithms and other non-blocking logic can run here
}