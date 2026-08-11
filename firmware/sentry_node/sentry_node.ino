#include <ArduinoJson.h>

// ==============================================================================
// SENTRY NODE FIRMWARE (Cloud Viability Monitor & State Machine)
// ==============================================================================
// This Arduino acts as the decentralized "Brain" of the mesh.
// It tracks network health based on measured Pi telemetry and drives state 
// transitions strictly using events and hysteresis, completely abandoning 
// fixed-duration timers.
// ==============================================================================

String current_state = "CLOUD";

// Tunable parameters from host (for sweeping)
int K_passes_required = 3;
unsigned long DWELL_MS = 1000;

// Tracking
int consecutive_cloud_up = 0;
unsigned long first_cloud_up_time = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) { ; }
  Serial.println("{\"status\": \"SENTRY_ONLINE\", \"state\": \"CLOUD\"}");
}

void loop() {
  if (Serial.available() > 0) {
    String payload = Serial.readStringUntil('\n');
    payload.trim();

    // Configuration Sweep Injection
    if (payload.startsWith("CONFIG:")) {
      sscanf(payload.c_str(), "CONFIG:%d,%lu", &K_passes_required, &DWELL_MS);
      Serial.print("{\"status\": \"CONFIGURED\", \"K\":");
      Serial.print(K_passes_required);
      Serial.print(", \"DWELL_MS\":");
      Serial.print(DWELL_MS);
      Serial.println("}");
      return;
    }
    
    // Explicit completion signal from Crypto Node (Not a timer!)
    if (payload == "BOOTSTRAP_COMPLETE" && current_state == "ZKP_BOOTSTRAP") {
      current_state = "ECC_STEADY";
      Serial.println("{\"transition\": \"ECC_STEADY\", \"reason\": \"CRYPTO_READY\"}");
      return;
    }

    // Network Health Events emitted by the Pi's active probing
    if (payload == "CLOUD_DOWN") {
      consecutive_cloud_up = 0;
      first_cloud_up_time = 0;
      
      if (current_state == "CLOUD") {
        current_state = "ZKP_BOOTSTRAP";
        Serial.println("{\"transition\": \"ZKP_BOOTSTRAP\", \"reason\": \"NETWORK_LOSS\"}");
      }
    } 
    else if (payload == "CLOUD_UP") {
      if (current_state == "ECC_STEADY") {
        if (consecutive_cloud_up == 0) {
          first_cloud_up_time = millis();
        }
        
        consecutive_cloud_up++;
        unsigned long stable_duration = millis() - first_cloud_up_time;
        
        // Hysteresis Gate: K consecutive passes AND minimum Dwell time
        if (consecutive_cloud_up >= K_passes_required && stable_duration >= DWELL_MS) {
           // Output the command for the Pi to initiate the Rejoin Sequence.
           // The safety invariant dictates we DO NOT change state to CLOUD until 
           // the Pi confirms the cloud has actually accepted authority.
           Serial.println("{\"cmd\": \"INITIATE_REJOIN\", \"reason\": \"CLOUD_STABLE\"}");
        }
      }
    }
    
    // Confirmation from Pi that Cloud accepted authority (Step 3 of safety fix)
    if (payload == "REJOIN_CONFIRMED" && current_state == "ECC_STEADY") {
      current_state = "CLOUD";
      Serial.println("{\"transition\": \"CLOUD\", \"reason\": \"AUTHORITY_HANDOFF_SUCCESS\"}");
    }
    
    // If Rejoin fails, the Pi informs us to stay in Edge mode
    if (payload == "REJOIN_FAILED" && current_state == "ECC_STEADY") {
      consecutive_cloud_up = 0;
      first_cloud_up_time = 0;
      Serial.println("{\"log\": \"REJOIN_FAILED_STAYING_IN_EDGE_MODE\"}");
    }
  }
}
