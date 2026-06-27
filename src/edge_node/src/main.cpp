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

// Trust Score Configuration (Phase 2.5)
int trust_score = 100;
const int EWMA_ALPHA = 50; // 50% weight for new observations
int sim_performance = 100;
bool node_evicted = false;

void update_trust_score(int current_performance) {
  // Integer arithmetic EWMA to avoid expensive floating-point operations
  trust_score = ((EWMA_ALPHA * current_performance) + ((100 - EWMA_ALPHA) * trust_score)) / 100;
}

float profile_disclosure_single(int bytes) {
  uint8_t private_key[uECC_BYTES];
  uint8_t public_key[uECC_BYTES * 2];
  uECC_set_rng(&RNG);
  
  // Reset cycle counter
  ARM_DWT_CYCCNT = 0;
  uint32_t start_cycles = ARM_DWT_CYCCNT;
  
  // Base ECDSA execution
  uECC_make_key(public_key, private_key);
  
  // Phase 2.5B Hypothesis Testing: We inject 'algorithmic jitter' by randomizing the multiplier.
  // Instead of one random multiplier for the whole payload, we roll a new random complexity 
  // for EACH individual byte (attribute) in the payload, simulating independent ZKP attributes.
  volatile uint32_t dummy = 0;
  for(int i = 0; i < bytes; i++) {
     // Each attribute draws a random complexity multiplier between 5,000 and 16,999
     int attribute_complexity = (rand() % 12000) + 5000;
     for(int j = 0; j < attribute_complexity; j++) {
        dummy += (j % 3);
     }
  }
  
  uint32_t end_cycles = ARM_DWT_CYCCNT;
  uint32_t diff = end_cycles - start_cycles;
  float latency_ms = (float)diff / 64000.0;
  
  Serial.print("{\"topic\": \"crypto_profile\", \"algorithm\": \"zkp_sweep\", \"payload_bytes\": ");
  Serial.print(bytes);
  Serial.print(", \"cycles\": ");
  Serial.print(diff);
  Serial.print(", \"latency_ms\": ");
  Serial.print(latency_ms);
  Serial.println("}");
  
  return latency_ms;
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
  
  // Phase 2.4B: Consume incoming dummy network interrupts to clear the hardware RingBuffer
  // The actual CPU jitter occurs when the hardware UART IRQ fires during the cryptography execution.
  while (Serial.available() > 0) {
      Serial.read();
  }
  
  // Maintain the baseline heartbeat logic
  if (current_time - last_heartbeat >= 1000) {
    last_heartbeat = current_time;
    
    Serial.print("{\"topic\": \"heartbeat\", \"data\": ");
    Serial.print(counter);
    Serial.println("}");
    
    counter++;
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
  
  // Run ONE selective disclosure profiling payload every 1 second
  static unsigned long last_profile_time = 0;
  static int payload_idx = 0;
  static int cycle_count = 0;
  int payload_sizes[] = {1, 8, 32, 64}; // Removed 128 and 256
  
  if (current_time - last_profile_time >= 1000 && counter > 2) {
    last_profile_time = current_time;
    
    int current_bytes = payload_sizes[payload_idx];
    float last_latency = profile_disclosure_single(current_bytes);
    
    // Dynamically calculate node performance based on latency
    // If latency > 500ms (ISO safety threshold), performance drops to 0.
    // If latency < 150ms, performance is 100.
    if (last_latency >= 500.0) {
        sim_performance = 0;
    } else if (last_latency <= 150.0) {
        sim_performance = 100;
    } else {
        sim_performance = 100 - (int)(((last_latency - 150.0) / 350.0) * 100.0);
    }
    
    // Process Trust Score simulation
    if (node_evicted) {
       // Node remains evicted for the rest of this payload's 8-cycle duration
       Serial.print("{\"topic\": \"eviction_hold\", \"node\": \"simulated_node\", \"score\": ");
       Serial.print(trust_score);
       Serial.println("}");
    } else {
       update_trust_score(sim_performance);
       
       if (trust_score < 30) {
          Serial.print("{\"topic\": \"eviction\", \"node\": \"simulated_node\", \"score\": ");
          Serial.print(trust_score);
          Serial.println("}");
          node_evicted = true;
       } else {
          Serial.print("{\"topic\": \"trust_score\", \"node\": \"simulated_node\", \"score\": ");
          Serial.print(trust_score);
          Serial.println("}");
       }
    }
    
    // Advance cycle count
    cycle_count++;
    if (cycle_count >= 8) {
       // 8 cycles completed for this payload size. Move to next size and reset node.
       cycle_count = 0;
       payload_idx = (payload_idx + 1) % 4;
       
       sim_performance = 100;
       trust_score = 100;
       node_evicted = false;
       Serial.println("{\"topic\": \"trust_score_reset\", \"reason\": \"next_payload_size\"}");
    }
  }
}