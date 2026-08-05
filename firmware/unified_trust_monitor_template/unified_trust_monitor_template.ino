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

// Cryptographic Global State
const float EVICTION_THRESHOLD = 30.0;
float trust_score = 100.0;
int cycle_count = 0;
bool attack_mode_active = false;

// ARM Cortex-M4 DWT Registers for precision cycle counting
#define ARM_DWT_CYCCNT    (*(volatile uint32_t *)0xE0001004)
#define ARM_DWT_CTRL      (*(volatile uint32_t *)0xE0001000)
#define ARM_DEMCR         (*(volatile uint32_t *)0xE000EDFC)
#define ARM_DEMCR_TRCENA  (1 << 24)
#define ARM_DWT_CTRL_CYCCNTENA (1 << 0)

#include <uECC.h>

static int RNG(uint8_t *dest, unsigned size) {
  while (size) {
    uint8_t val = (uint8_t)rand();
    *dest = val;
    ++dest;
    --size;
  }
  return 1;
}

// Simulated cryptographic pointers
bool is_zkp_active = false;
bool is_ecc_active = false;

// Hardware Safeties
const int SAFETY_PIN = 12; // 24V PNP Optocoupler Bypass

void setup() {
  Serial.begin(115200);
  pinMode(SAFETY_PIN, OUTPUT);
  digitalWrite(SAFETY_PIN, LOW); // Start in safe state (Category 0 Halt)
  
  // Enable DWT Cycle Counter hardware register
  ARM_DEMCR |= ARM_DEMCR_TRCENA;
  ARM_DWT_CTRL |= ARM_DWT_CTRL_CYCCNTENA;
  
  uECC_set_rng(&RNG);

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
// ------------------------------------------------------------------------------

void execute_ecc_verification() {
  uint8_t private_key[uECC_BYTES];
  uint8_t public_key[uECC_BYTES * 2];
  
  ARM_DWT_CYCCNT = 0;
  uint32_t start_cycles = ARM_DWT_CYCCNT;
  
  // Base ECC Payload (1 loop = ~111.5ms on Cortex-M4)
  uECC_make_key(public_key, private_key);
  
  if (attack_mode_active) {
    for(int i = 0; i < 7; i++) {
      uECC_make_key(public_key, private_key);
    }
  }
  
  uint32_t end_cycles = ARM_DWT_CYCCNT;
  float exec_time_ms = (float)(end_cycles - start_cycles) / 64000.0;
  
  float current_trust = 100.0;
  // Calibrated Threshold: 150.0ms (gives ~38ms of hardware jitter headroom)
  if (exec_time_ms > 150.0) {
    float penalty = (float)(exec_time_ms - 150.0);
    current_trust = max(0.0f, 100.0f - penalty); 
  }
  
  trust_score = (ewma_alpha * current_trust) + ((1.0 - ewma_alpha) * trust_score);
  
  if (trust_score < EVICTION_THRESHOLD) {
    digitalWrite(SAFETY_PIN, LOW); // Trigger Category 0 Halt
  }
  
  Serial.print("{\"cycle\": ");
  Serial.print(cycle_count);
  Serial.print(", \"exec_time_ms\": ");
  Serial.print(exec_time_ms);
  Serial.print(", \"trust_score\": ");
  Serial.print(trust_score);
  Serial.println("}");
  
  cycle_count++;
  delay(10);
}

void execute_zkp_verification() {
  uint8_t private_key[uECC_BYTES];
  uint8_t public_key[uECC_BYTES * 2];
  
  ARM_DWT_CYCCNT = 0;
  uint32_t start_cycles = ARM_DWT_CYCCNT;
  
  // Base ZKP Payload (Simulated via 3x ECC workload = ~334.5ms)
  // This perfectly fits right under your 400ms threshold bound!
  for(int i = 0; i < 3; i++) {
    uECC_make_key(public_key, private_key);
  }
  
  if (attack_mode_active) {
    for(int i = 0; i < 6; i++) {
      uECC_make_key(public_key, private_key);
    }
  }
  
  uint32_t end_cycles = ARM_DWT_CYCCNT;
  float exec_time_ms = (float)(end_cycles - start_cycles) / 64000.0;
  
  float current_trust = 100.0;
  // Original Threshold: 400.0ms (gives ~65ms of hardware jitter headroom)
  if (exec_time_ms > 400.0) {
    float penalty = (float)(exec_time_ms - 400.0);
    current_trust = max(0.0f, 100.0f - penalty); 
  }
  
  trust_score = (ewma_alpha * current_trust) + ((1.0 - ewma_alpha) * trust_score);
  
  if (trust_score < EVICTION_THRESHOLD) {
    digitalWrite(SAFETY_PIN, LOW); // Trigger Category 0 Halt
  }
  
  Serial.print("{\"cycle\": ");
  Serial.print(cycle_count);
  Serial.print(", \"exec_time_ms\": ");
  Serial.print(exec_time_ms);
  Serial.print(", \"trust_score\": ");
  Serial.print(trust_score);
  Serial.println("}");
  
  cycle_count++;
  delay(10);
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
        attack_mode_active = true;
      } else if (input_buffer.startsWith("{") && input_buffer.endsWith("}")) {
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, input_buffer);
        if (!error && doc.containsKey("algo") && doc.containsKey("alpha")) {
          // Reset the entire state machine!
          current_algo = doc["algo"].as<String>();
          ewma_alpha = doc["alpha"].as<float>();
          trust_score = 100.0;
          cycle_count = 0;
          attack_mode_active = false;
          
          if (current_algo == "ZKP") {
            is_zkp_active = true;
            is_ecc_active = false;
          } else if (current_algo == "ECC") {
            is_zkp_active = false;
            is_ecc_active = true;
          }
          
          digitalWrite(SAFETY_PIN, HIGH);
          Serial.println("{\"status\": \"READY\"}");
        }
      }
      
      input_buffer = ""; // Clear buffer for next command
    } else {
      input_buffer += c;
      if (input_buffer.length() > 200) input_buffer = "";
    }
  }

  // 2. Continuous Mathematical Verification & Safety Watchdog
  if (is_zkp_active) {
    execute_zkp_verification();
  } else if (is_ecc_active) {
    execute_ecc_verification();
  }
}
