// Cryptographic Edge Node - Phase 2 ZKP & EWMA Trust Score
// Hardware: Arduino Nano 33 BLE
// Flashed via Arduino IDE

float trust_score = 100.0;
const float EWMA_ALPHA = 0.3; // Smoothing factor
int cycle = 0;

void setup() {
  Serial.begin(115200);
  
  // Wait for serial monitor or Pi to connect
  while (!Serial); 
}

void loop() {
  // 1. Simulate a Zero-Knowledge Proof computation
  // Normally this takes ~45ms on the Nano 33 BLE.
  unsigned long start_time = millis();
  
  // Simulate standard cryptographic workload
  delay(45); 
  
  // Check if we received a payload trigger over Serial (simulating an attack or lag)
  if (Serial.available() > 0) {
    String payload = Serial.readStringUntil('\n');
    if (payload.length() > 64) {
      // 256-byte Malicious Payload Triggered!
      // This forces the ZKP computation to lag significantly.
      delay(550); // Simulate heavy cryptographic delay
    }
  }
  
  unsigned long exec_time = millis() - start_time;

  // 2. Calculate EWMA Trust Score
  float current_trust = 100.0;
  if (exec_time > 100) {
    // If it takes longer than 100ms, trust begins to plummet
    current_trust = max(0.0, 100.0 - (exec_time - 100)); 
  }
  
  trust_score = (EWMA_ALPHA * current_trust) + ((1.0 - EWMA_ALPHA) * trust_score);

  // 3. Spit out the JSON for the Raspberry Pi to read
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
