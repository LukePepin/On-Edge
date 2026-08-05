#include <ArduinoJson.h>

// ==============================================================================
// Unified Trust Monitor Firmware (Dynamic Serial Configuration)
// ==============================================================================
// This template accepts dynamic algorithm and alpha parameterization over Serial
// upon boot. Drop your existing ECC and ZKP mathematical verification blocks 
// into the respective functions below.
// ==============================================================================

// Global State
String current_algo = "UNKNOWN";
float ewma_alpha = 0.3; // Default alpha

// Simulated cryptographic pointers
bool is_zkp_active = false;
bool is_ecc_active = false;

// Hardware Safeties
const int SAFETY_PIN = 12; // 24V PNP Optocoupler Bypass

void setup() {
  Serial.begin(115200);
  pinMode(SAFETY_PIN, OUTPUT);
  digitalWrite(SAFETY_PIN, LOW); // Start in safe state (Category 0 Halt)

  // Wait for serial connection
  while (!Serial) {
    ; 
  }

  // --- DYNAMIC SERIAL CONFIGURATION HANDSHAKE ---
  // Block until the Pi Supervisor sends the configuration payload
  bool configured = false;
  while (!configured) {
    if (Serial.available() > 0) {
      String payload = Serial.readStringUntil('\n');
      payload.trim();
      
      if (payload.startsWith("{") && payload.endsWith("}")) {
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, payload);

        if (!error) {
          if (doc.containsKey("algo") && doc.containsKey("alpha")) {
            current_algo = doc["algo"].as<String>();
            ewma_alpha = doc["alpha"].as<float>();
            
            // Set memory pointers based on chosen algorithm
            if (current_algo == "ZKP") {
              is_zkp_active = true;
              is_ecc_active = false;
            } else if (current_algo == "ECC") {
              is_zkp_active = false;
              is_ecc_active = true;
            }

            configured = true;
            
            // Reply with the exact JSON string the Python node is expecting
            Serial.println("{\"status\": \"READY\"}");
            
            // Re-energize the physical safeguard loop to allow motion
            digitalWrite(SAFETY_PIN, HIGH);
          }
        }
      }
    }
  }
}

// ------------------------------------------------------------------------------
// Cryptographic Blocks
// Drop your existing code from `firmware/ecc_trust_monitor` and 
// `firmware/zkp_trust_monitor` into these functions.
// ------------------------------------------------------------------------------

void execute_ecc_verification() {
  // TODO: Insert your ECDSA verification logic here
  // Ensure you use the DWT_CYCCNT registers for cycle-accurate profiling
  
  // Example EWMA update:
  // float trust_score = (ewma_alpha * old_trust) + ((1.0 - ewma_alpha) * success);
}

void execute_zkp_verification() {
  // TODO: Insert your Schnorr selective disclosure proof logic here
  // Remember to segment the payload into 64-byte chunks to invoke Berry-Esseen bounds
  
  // Example EWMA update:
  // float trust_score = (ewma_alpha * old_trust) + ((1.0 - ewma_alpha) * success);
}

// ------------------------------------------------------------------------------
// Main Loop
// ------------------------------------------------------------------------------
String input_buffer = "";

void loop() {
  // 1. Listen for "ATTACK\n" from the Python Supervisor (NON-BLOCKING)
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      input_buffer.trim();
      
      if (input_buffer == "ATTACK") {
        // 2. Route the verification to the dynamically configured memory block
        if (is_zkp_active) {
          execute_zkp_verification();
        } else if (is_ecc_active) {
          execute_ecc_verification();
        }
        
        // 3. Serialize and broadcast the updated telemetry back to Python
        // Example: Serial.println("{\"trust_score\": 90.0}");
      }
      
      input_buffer = ""; // Clear buffer for next command
    } else {
      // Accumulate characters
      input_buffer += c;
      
      // Safety bound to prevent memory exhaustion on malformed data
      if (input_buffer.length() > 50) {
        input_buffer = "";
      }
    }
  }
}
