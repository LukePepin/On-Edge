#include <Arduino.h>
#include <uECC.h>

#define LED_PIN 13

// ARM Cortex-M4 DWT Registers for precision cycle counting
#define ARM_DWT_CYCCNT    (*(volatile uint32_t *)0xE0001004)
#define ARM_DWT_CTRL      (*(volatile uint32_t *)0xE0001000)
#define ARM_DEMCR         (*(volatile uint32_t *)0xE000EDFC)
#define ARM_DEMCR_TRCENA  (1 << 24)
#define ARM_DWT_CTRL_CYCCNTENA (1 << 0)

unsigned long last_heartbeat = 0;
int counter = 0;
bool profiling_done = false;

// Custom RNG for uECC (required for key generation)
static int RNG(uint8_t *dest, unsigned size) {
  // Simple LCG for testing. In production on nRF52840, we will use the hardware TRNG.
  while (size) {
    uint8_t val = (uint8_t)rand();
    *dest = val;
    ++dest;
    --size;
  }
  return 1;
}

void profile_ecdsa_keygen() {
  uint8_t private_key[uECC_BYTES];
  uint8_t public_key[uECC_BYTES * 2];
  
  uECC_set_rng(&RNG);
  
  // Reset the cycle counter to avoid overflow during measurement
  ARM_DWT_CYCCNT = 0;
  
  // Capture start cycle
  uint32_t start_cycles = ARM_DWT_CYCCNT;
  
  // Execute constant-time cryptography (Mbed native uECC API)
  uECC_make_key(public_key, private_key);
  
  // Capture end cycle
  uint32_t end_cycles = ARM_DWT_CYCCNT;
  
  uint32_t diff = end_cycles - start_cycles;
  float latency_ms = (float)diff / 64000.0; // Nano 33 BLE runs at 64 MHz (64,000 cycles per ms)
  
  Serial.print("{\"topic\": \"crypto_profile\", \"algorithm\": \"ecdsa_keygen\", \"cycles\": ");
  Serial.print(diff);
  Serial.print(", \"latency_ms\": ");
  Serial.print(latency_ms);
  Serial.println("}");
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  
  Serial.begin(115200);
  
  // Enable DWT Cycle Counter hardware register
  ARM_DEMCR |= ARM_DEMCR_TRCENA;
  ARM_DWT_CTRL |= ARM_DWT_CTRL_CYCCNTENA;
  
  delay(2000);
}

void loop() {
  unsigned long current_time = millis();
  
  // Maintain the baseline heartbeat logic
  if (current_time - last_heartbeat >= 1000) {
    last_heartbeat = current_time;
    
    Serial.print("{\"topic\": \"heartbeat\", \"data\": ");
    Serial.print(counter);
    Serial.println("}");
    
    counter++;
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
  
  // Run the profiling routine continuously every 2 seconds
  static unsigned long last_profile_time = 0;
  if (current_time - last_profile_time >= 2000 && counter > 2) {
    last_profile_time = current_time;
    profile_ecdsa_keygen();
  }
}