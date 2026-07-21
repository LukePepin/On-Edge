#include <Arduino.h>

// Cryptographic Edge Node - Phase 2 ZKP & EWMA Trust Score
// Hardware: Arduino Nano 33 BLE
// Flashed via VS Code PlatformIO

float trust_score = 100.0;
const float EWMA_ALPHA = 0.3; // Smoothing factor
const float EVICTION_THRESHOLD = 30.0; // Fail-Safe trigger threshold
const int HARDWARE_BYPASS_PIN = 2; // D2 connected to Optocoupler Boards A & B
int cycle = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize the Optocoupler Bypass Pin
  pinMode(HARDWARE_BYPASS_PIN, OUTPUT);
  // FAIL-SAFE DESIGN: Default to HIGH (24V active) so the UR5 is allowed to move.
  digitalWrite(HARDWARE_BYPASS_PIN, HIGH); 
  
}

void loop() {
  // 1. Simulate a Zero-Knowledge Proof computation
  unsigned long start_time = millis();
  
  // Simulate standard cryptographic workload
  delay(325); 
  
  // Check if we received a payload trigger over Serial (simulating an attack or lag)
  if (Serial.available() > 0) {
    String payload = Serial.readStringUntil('\n');
    if (payload.length() > 64) {
      // 256-byte Malicious Payload Triggered!
      delay(550); // Simulate heavy cryptographic delay
    }
  }
  
  unsigned long exec_time = millis() - start_time;

  // 2. Calculate EWMA Trust Score
  float current_trust = 100.0;
  if (exec_time > 400) {
    // 400ms threshold: Anything under 400ms (like our 325ms baseline) is 100% trusted.
    // An attack that spikes execution to 550ms+ will instantly drop trust to 0.
    float penalty = (float)(exec_time - 400);
    current_trust = max(0.0f, 100.0f - penalty); 
  }
  
  trust_score = (EWMA_ALPHA * current_trust) + ((1.0 - EWMA_ALPHA) * trust_score);

  // 3. HARDWARE CATEGORY 0 HALT LOGIC
  if (trust_score < EVICTION_THRESHOLD) {
    // Drop the pin to 0V. The Optocouplers will instantly kill the 24V UR5 loops!
    digitalWrite(HARDWARE_BYPASS_PIN, LOW);
  } else {
    // Network is safe. Keep the 24V loop closed so the robot can operate.
    digitalWrite(HARDWARE_BYPASS_PIN, HIGH);
  }

  // 4. Spit out the JSON for the Raspberry Pi to read
  Serial.print("{\"cycle\": ");
  Serial.print(cycle);
  Serial.print(", \"exec_time_ms\": ");
  Serial.print(exec_time);
  Serial.print(", \"trust_score\": ");
  Serial.print(trust_score);
  Serial.println("}");

  cycle++;
  delay(10); // Very short delay before next cycle
}
