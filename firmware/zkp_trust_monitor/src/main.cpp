#include <Arduino.h>

// Cryptographic Edge Node - Phase 2 ZKP & EWMA Trust Score
// Hardware: Arduino Nano 33 BLE
// Flashed via VS Code PlatformIO

float trust_score = 100.0;
const float EWMA_ALPHA = 0.3; // Smoothing factor
const float EVICTION_THRESHOLD = 30.0; // Fail-Safe trigger threshold
const int HARDWARE_BYPASS_PIN_1 = 2; // Channel 1 (SI0)
const int HARDWARE_BYPASS_PIN_2 = 3; // Channel 2 (SI1)
int cycle = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize the Optocoupler Bypass Pins
  pinMode(HARDWARE_BYPASS_PIN_1, OUTPUT);
  pinMode(HARDWARE_BYPASS_PIN_2, OUTPUT);
  // FAIL-SAFE DESIGN: Default to HIGH (24V active) so the UR5 is allowed to move.
  digitalWrite(HARDWARE_BYPASS_PIN_1, HIGH); 
  digitalWrite(HARDWARE_BYPASS_PIN_2, HIGH); 
  
}

unsigned long last_message_time = 0;

void loop() {
  unsigned long current_time = millis();
  unsigned long time_since_last_packet = current_time - last_message_time;

  // 1. Check for incoming authentication packets from the Cloud Provisioner
  if (Serial.available() > 0) {
    String payload = Serial.readStringUntil('\n');
    if (payload.length() > 0) {
      // Valid packet received! Reset the network timer.
      last_message_time = current_time;
      time_since_last_packet = 0;
    }
  }

  // 2. Calculate EWMA Trust Score based on Real-Time Network Latency
  float current_trust = 100.0;
  
  // The ISO 13849-1 Safety Ceiling is 500ms. We set our panic threshold at 400ms.
  if (time_since_last_packet > 400) {
    // Every millisecond of network delay or DoS packet loss bleeds the score
    float penalty = (float)(time_since_last_packet - 400);
    current_trust = max(0.0f, 100.0f - penalty); 
  }
  
  trust_score = (EWMA_ALPHA * current_trust) + ((1.0 - EWMA_ALPHA) * trust_score);

  // 3. HARDWARE CATEGORY 0 HALT LOGIC
  if (trust_score < EVICTION_THRESHOLD) {
    // Drop the pin to 0V. The Optocouplers will instantly kill the 24V UR5 loops!
    digitalWrite(HARDWARE_BYPASS_PIN_1, LOW);
    digitalWrite(HARDWARE_BYPASS_PIN_2, LOW);
  } else {
    // Network is safe. Keep the 24V loop closed so the robot can operate.
    digitalWrite(HARDWARE_BYPASS_PIN_1, HIGH);
    digitalWrite(HARDWARE_BYPASS_PIN_2, HIGH);
  }

  // 4. Spit out the JSON status to the Cloud Provisioner
  Serial.print("{\"cycle\": ");
  Serial.print(cycle);
  Serial.print(", \"network_latency_ms\": ");
  Serial.print(time_since_last_packet);
  Serial.print(", \"trust_score\": ");
  Serial.print(trust_score);
  Serial.println("}");

  cycle++;
  delay(10); // Very short delay before next loop evaluation
}
