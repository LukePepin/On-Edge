#include <ArduinoJson.h>

// ==============================================================================
// SENTRY NODE FIRMWARE (Node B - Cloud Viability Monitor)
// ==============================================================================
// This secondary Arduino acts as the decentralized "Brain" of the mesh.
// It tracks network outage durations and mathematically determines when the 
// Crypto Node (Node A) should transition from ZKP to ECC, and when the Pi 
// is allowed to safely rejoin the Cloud.
// ==============================================================================

String current_state = "IDLE";
unsigned long outage_start_time = 0;
const unsigned long ZKP_DURATION_MS = 5000;   // 5 seconds of ZKP initialization
const unsigned long ECC_DURATION_MS = 10000;  // 10 seconds of ECC continuous
// Total Outage = 15 seconds for the video demonstration (scales to 60s in production)

void setup() {
  Serial.begin(115200);
  while (!Serial) { ; }
  Serial.println("{\"status\": \"SENTRY_ONLINE\"}");
}

void loop() {
  // Listen for Pi Orchestrator telling us the Cloud TCP Socket dropped
  if (Serial.available() > 0) {
    String payload = Serial.readStringUntil('\n');
    payload.trim();
    
    if (payload == "JAMMED" && current_state == "IDLE") {
      current_state = "ZKP_PHASE";
      outage_start_time = millis();
      
      // Command the Pi to initialize the Crypto Arduino with ZKP
      Serial.println("{\"cmd\": \"START_ZKP\", \"reason\": \"NETWORK_LOSS_DETECTED\"}");
    }
  }

  // Autonomous Edge Mesh State Machine
  if (current_state != "IDLE") {
    unsigned long elapsed_outage = millis() - outage_start_time;
    
    if (current_state == "ZKP_PHASE") {
      // Print reconnect progress every second
      if (elapsed_outage % 1000 < 50) {
        Serial.print("{\"progress\": \"ZKP_INIT\", \"elapsed_ms\": ");
        Serial.print(elapsed_outage);
        Serial.println("}");
        delay(50); // debounce print
      }
      
      if (elapsed_outage >= ZKP_DURATION_MS) {
        current_state = "ECC_PHASE";
        // Command the Pi to hot-swap the Crypto Arduino to ECC
        Serial.println("{\"cmd\": \"START_ECC\", \"reason\": \"IDENTITY_SECURED\"}");
      }
      
    } else if (current_state == "ECC_PHASE") {
      if (elapsed_outage % 1000 < 50) {
        Serial.print("{\"progress\": \"ECC_ACTIVE\", \"elapsed_ms\": ");
        Serial.print(elapsed_outage);
        Serial.println("}");
        delay(50);
      }
      
      if (elapsed_outage >= (ZKP_DURATION_MS + ECC_DURATION_MS)) {
        current_state = "IDLE";
        // Command the Pi to restore the physical Cloud TCP socket
        Serial.println("{\"cmd\": \"REJOIN_CLOUD\", \"reason\": \"VIABILITY_RESTORED\"}");
      }
    }
  }
}
