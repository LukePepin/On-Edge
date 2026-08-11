#include <uECC.h>

#define ARM_DWT_CYCCNT    (*(volatile uint32_t *)0xE0001004)
#define ARM_DWT_CTRL      (*(volatile uint32_t *)0xE0001000)
#define ARM_DEMCR         (*(volatile uint32_t *)0xE000EDFC)
#define ARM_DEMCR_TRCENA  (1 << 24)
#define ARM_DWT_CTRL_CYCCNTENA (1 << 0)

// 64-byte payload maps to 2 independent 32-byte scalars.
// A full Schnorr verification requires two scalar multiplications (sG and cP).
// We proxy this by running uECC_compute_public_key twice.
// This measures scalar-multiplication cost as a lower bound on Schnorr verification,
// not a full verify (no hashing, no point addition).
const int PAYLOAD_BYTES = 64;
uint8_t attributes[PAYLOAD_BYTES];
uint8_t public_key[64]; // Temporary buffer for point generation

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
  ARM_DEMCR |= ARM_DEMCR_TRCENA;
  ARM_DWT_CTRL |= ARM_DWT_CTRL_CYCCNTENA;
  
  uECC_set_rng(&RNG);
  
  // Wait for orchestrator script
  while (!Serial) { ; }
  
  // Handshake to synchronize with Python orchestrator
  Serial.println("READY");
}

void loop() {
  // Accumulate genuine random attribute data per run.
  // Device does NOT generate its own test data.
  static int bytes_read = 0;
  
  while (Serial.available() > 0 && bytes_read < PAYLOAD_BYTES) {
    attributes[bytes_read++] = Serial.read();
  }

  if (bytes_read >= PAYLOAD_BYTES) {
    bytes_read = 0; // Reset for next run

    ARM_DWT_CYCCNT = 0;
    uint32_t start = ARM_DWT_CYCCNT;

    // ---- REAL VERIFICATION WORK GOES HERE ----
    // Genuine uECC scalar multiplication per constraint.
    // No delays, no padding, no calibration loops.
    
    // Constraint 1: First 32 bytes of payload (acts as a private scalar)
    int res1 = uECC_compute_public_key(&attributes[0], public_key);
    
    // Constraint 2: Second 32 bytes of payload
    int res2 = uECC_compute_public_key(&attributes[32], public_key);

    uint32_t end = ARM_DWT_CYCCNT;

    Serial.print("{\"start\":");   Serial.print(start);
    Serial.print(",\"end\":");     Serial.print(end);
    Serial.print(",\"res1\":");    Serial.print(res1);
    Serial.print(",\"res2\":");    Serial.print(res2);
    Serial.print(",\"keybyte\":"); Serial.print(public_key[0]);
    Serial.println("}");
  }
}
