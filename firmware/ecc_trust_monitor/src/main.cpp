#include <Arduino.h>
#include <uECC.h>

// Cryptographic Edge Node - Phase 3.5 ECC & EWMA Trust Score
// Hardware: Arduino Nano 33 BLE
// Flashed via VS Code PlatformIO

float trust_score = 100.0;
const float EWMA_ALPHA = 0.5; // AGGRESSIVE 50% smoothing factor (Academic fix)
const float EVICTION_THRESHOLD = 30.0; // Fail-Safe trigger threshold
const int HARDWARE_BYPASS_PIN = 2; // D2 connected to Optocoupler Boards A & B
int cycle = 0;

// ARM Cortex-M4 DWT Registers for precision cycle counting (Academic fix)
#define ARM_DWT_CYCCNT    (*(volatile uint32_t *)0xE0001004)
#define ARM_DWT_CTRL      (*(volatile uint32_t *)0xE0001000)
#define ARM_DEMCR         (*(volatile uint32_t *)0xE000EDFC)
#define ARM_DEMCR_TRCENA  (1 << 24)
#define ARM_DWT_CTRL_CYCCNTENA (1 << 0)

// Custom RNG for uECC (required for key generation)
static int RNG(uint8_t *dest, unsigned size) {
  while (size) {
    uint8_t val = (uint8_t)rand();
    *dest = val;
    ++dest;
    --size;
  }
  return 1;
}

void setup() {
  Serial.begin(115200);
  
  // Enable DWT Cycle Counter hardware register
  ARM_DEMCR |= ARM_DEMCR_TRCENA;
  ARM_DWT_CTRL |= ARM_DWT_CTRL_CYCCNTENA;
  
  // Initialize the Optocoupler Bypass Pin
  pinMode(HARDWARE_BYPASS_PIN, OUTPUT);
  digitalWrite(HARDWARE_BYPASS_PIN, HIGH); // Default to HIGH (24V active)
  
  uECC_set_rng(&RNG);
}

void loop() {
  uint8_t private_key[uECC_BYTES];
  uint8_t public_key[uECC_BYTES * 2];
  
  // Reset cycle counter
  ARM_DWT_CYCCNT = 0;
  uint32_t start_cycles = ARM_DWT_CYCCNT;
  
  // 1. Execute REAL ECC Baseline Computation (Academic fix)
  uECC_make_key(public_key, private_key);
  
  // Check if we received a payload trigger over Serial (simulating a degraded/byzantine attack)
  if (Serial.available() > 0) {
    String payload = Serial.readStringUntil('\n');
    payload.trim(); 
    if (payload == "ATTACK") {
      // Simulate heavy cryptographic Byzantine attack by looping MSMs
      for(int i = 0; i < 7; i++) {
        uECC_make_key(public_key, private_key);
      }
    }
  }
  
  uint32_t end_cycles = ARM_DWT_CYCCNT;
  uint32_t diff = end_cycles - start_cycles;
  float exec_time_ms = (float)diff / 64000.0; // 64 MHz M4 clock

  // 2. Calculate EWMA Trust Score
  float current_trust = 100.0;
  if (exec_time_ms > 100.0) {
    // 100ms threshold: Anything under 100ms is 100% trusted.
    float penalty = (float)(exec_time_ms - 100.0);
    current_trust = max(0.0f, 100.0f - penalty); 
  }
  
  trust_score = (EWMA_ALPHA * current_trust) + ((1.0 - EWMA_ALPHA) * trust_score);

  // 3. HARDWARE CATEGORY 0 HALT LOGIC
  if (trust_score < EVICTION_THRESHOLD) {
    digitalWrite(HARDWARE_BYPASS_PIN, LOW); // Kill the 24V loops
  } else {
    digitalWrite(HARDWARE_BYPASS_PIN, HIGH); // Network is safe
  }

  // 4. Spit out the JSON for the Raspberry Pi to read
  Serial.print("{\"cycle\": ");
  Serial.print(cycle);
  Serial.print(", \"exec_time_ms\": ");
  Serial.print(exec_time_ms);
  Serial.print(", \"trust_score\": ");
  Serial.print(trust_score);
  Serial.println("}");

  cycle++;
  delay(10); // Short delay before next hardware cycle
}
