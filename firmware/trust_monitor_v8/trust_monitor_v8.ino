#include <ArduinoJson.h>

// ==============================================================================
// Trust Monitor V8 - bounded instrumentation of unified_trust_monitor_template.ino
// ==============================================================================
// UNCHANGED from firmware/unified_trust_monitor_template (V6/V7 source):
//   * workloads: "ECC" = uECC_make_key; "ZKP" = two uECC_compute_public_key calls on a
//     static device-generated buffer (a cost proxy; no proof is verified)
//   * DWT execution timing, exec_time_ms = cycles / 64000.0
//   * observation rules: ATTACK -> 0; otherwise 100 minus the execution-time penalty
//     above 150 ms (ECC) / 400 ms (ZKP)
//   * EWMA: trust = (alpha * obs) + ((1.0 - alpha) * trust)
//   * strict threshold trust < 30.0 -> digitalWrite(D12, LOW) on every such update
//   * D12 is raised only at boot and by a valid configuration (never by RECOVER)
//   * commands are read between workload cycles; ATTACK/RECOVER set/clear the flag;
//     a configuration resets trust (100), cycle (0) and the attack flag
//   * 115200 baud, delay(10) after each cycle
//
// ADDED (V8 instrumentation, protocol 1). One JSON object per line; every record has
//   "ev"   record type, "seq" per-boot record counter (+1 per record, detects losses),
//   "t_us" device micros() (32-bit, wraps every ~71.6 min; the host unwraps it).
//   boot   once when the serial connection opens: firmware identity and constants
//   hello  every 1 s while waiting for the first configuration
//   cfg    configuration applied (t_us = when it was processed)
//   cmd    ATTACK or RECOVER processed (state before/after, next cycle number)
//   upd    each trust update: t0_us (workload start), exec_ms (DWT), obs, trust (4 dp),
//          attack, below (trust < 30), d12 (commanded level after this update),
//          pw_us (duration of the previous upd record's Serial.write, -1 if none)
//   out    D12 commanded level changed: LOW at the first below-threshold update, HIGH when
//          a configuration raises it (t_us taken immediately before digitalWrite)
//   idle   1 s heartbeat while no workload is selected
//   err    rejected input: bad_json, bad_cfg, unknown_cmd, overflow
// Each record is formatted into one buffer and sent with ONE Serial.write() so that a
// report costs one USB write per cycle.
//
// NOT backward compatible with the historical logger on purpose: the old logger looks
// for "trust_score" and '"status": "READY"'; it will fail its handshake loudly instead of
// silently logging a stale trust value. The V8 host (v8/onedge_v8) reads this protocol and
// can also read the historical protocol in a degraded mode.
//
// Timestamps: t_us is the device clock only. The host never subtracts it from host times
// without an explicit clock-relationship estimate (v8/onedge_v8/clocks.py).
// ==============================================================================

static const char FW_NAME[] = "trust_monitor_v8";
static const char FW_VERSION[] = "8.0.0";
static const char FW_BUILD[] = __DATE__ " " __TIME__;
static const int PROTO_VERSION = 1;

// Global State (unchanged)
String current_algo = "UNKNOWN";
float ewma_alpha = 0.3; // Default alpha

// Cryptographic Global State (unchanged)
const float EVICTION_THRESHOLD = 30.0;
float trust_score = 100.0;
int cycle_count = 0;
bool attack_mode_active = false;

// Execution-time penalty thresholds, same values and double-literal semantics as the
// template's inline 150.0 / 400.0 comparisons.
const double ECC_PENALTY_MS = 150.0;
const double ZKP_PENALTY_MS = 400.0;

// ARM Cortex-M4 DWT Registers for precision cycle counting (unchanged)
#define ARM_DWT_CYCCNT    (*(volatile uint32_t *)0xE0001004)
#define ARM_DWT_CTRL      (*(volatile uint32_t *)0xE0001000)
#define ARM_DEMCR         (*(volatile uint32_t *)0xE000EDFC)
#define ARM_DEMCR_TRCENA  (1 << 24)
#define ARM_DWT_CTRL_CYCCNTENA (1 << 0)

#define uECC_CURVE uECC_secp256r1
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

// Simulated cryptographic pointers (unchanged)
bool is_zkp_active = false;
bool is_ecc_active = false;

// Hardware Safeties (unchanged)
const int SAFETY_PIN = 12; // 24V PNP Optocoupler Bypass

// ------------------------------------------------------------------------------
// V8 instrumentation state and record formatting
// ------------------------------------------------------------------------------
static uint32_t msg_seq = 0;        // record counter since boot
static bool d12_high = true;        // last level this firmware wrote to SAFETY_PIN
static uint32_t cfg_count = 0;      // accepted configurations since boot
static int32_t last_write_us = -1;  // duration of the previous upd record write
static bool out_low_pending = false;
static uint32_t out_low_t_us = 0;
static uint32_t last_idle_us = 0;

static char rec[256];
static size_t rec_len = 0;
static const size_t REC_LIMIT = sizeof(rec) - 3;   // room for "}\r\n"

static void rec_raw(const char *s) {
  while (*s && rec_len < REC_LIMIT) rec[rec_len++] = *s++;
}

static void rec_u32(uint32_t v) {
  char tmp[10];
  int i = 0;
  do { tmp[i++] = (char)('0' + (v % 10)); v /= 10; } while (v && i < 10);
  while (i && rec_len < REC_LIMIT) rec[rec_len++] = tmp[--i];
}

static void rec_i32(int32_t v) {
  if (v < 0) { rec_raw("-"); rec_u32((uint32_t)(-(int64_t)v)); }
  else rec_u32((uint32_t)v);
}

// Fixed-point decimal without printf float support. Non-finite values become null, which
// the host rejects as an invalid record instead of mis-parsing it.
static void rec_fixed(double x, int decimals) {
  if (isnan(x) || isinf(x)) { rec_raw("null"); return; }
  if (x < 0) { rec_raw("-"); x = -x; }
  uint32_t scale = 1;
  for (int i = 0; i < decimals; i++) scale *= 10;
  double scaled = x * (double)scale + 0.5;
  if (scaled >= 4.0e9) { rec_raw("null"); return; }
  uint32_t n = (uint32_t)scaled;
  rec_u32(n / scale);
  if (decimals > 0) {
    rec_raw(".");
    uint32_t frac = n % scale;
    for (uint32_t div = scale / 10; div > 0 && rec_len < REC_LIMIT; div /= 10) {
      rec[rec_len++] = (char)('0' + (frac / div) % 10);
    }
  }
}

static void rec_key(const char *key) { rec_raw(",\""); rec_raw(key); rec_raw("\":"); }

static void rec_str(const char *key, const char *val) {
  rec_key(key); rec_raw("\""); rec_raw(val); rec_raw("\"");
}

// Host-supplied text is limited to [A-Za-z0-9_] and 16 characters in records.
static void rec_safe_str(const char *key, const String &val) {
  rec_key(key); rec_raw("\"");
  for (unsigned i = 0; i < val.length() && i < 16 && rec_len < REC_LIMIT; i++) {
    char c = val.charAt(i);
    bool ok = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_';
    rec[rec_len++] = ok ? c : '?';
  }
  rec_raw("\"");
}

static void rec_begin(const char *ev, uint32_t t_us) {
  rec_len = 0;
  rec_raw("{\"ev\":\""); rec_raw(ev); rec_raw("\"");
  rec_key("seq"); rec_u32(msg_seq);
  rec_key("t_us"); rec_u32(t_us);
}

// Terminates and sends the record with a single write; returns the write duration (us).
static uint32_t rec_send() {
  rec[rec_len++] = '}';
  rec[rec_len++] = '\r';
  rec[rec_len++] = '\n';
  uint32_t t0 = micros();
  Serial.write((const uint8_t *)rec, rec_len);
  uint32_t dt = micros() - t0;
  msg_seq++;
  return dt;
}

static const char *workload_name() {
  if (is_zkp_active) return "ZKP";
  if (is_ecc_active) return "ECC";
  return "NONE";
}

static void report_identity(const char *ev) {
  rec_begin(ev, micros());
  rec_str("fw", FW_NAME);
  rec_str("ver", FW_VERSION);
  rec_str("build", FW_BUILD);
  rec_key("proto"); rec_i32(PROTO_VERSION);
  rec_key("thr"); rec_fixed(EVICTION_THRESHOLD, 4);
  rec_key("pen_ecc_ms"); rec_fixed(ECC_PENALTY_MS, 3);
  rec_key("pen_zkp_ms"); rec_fixed(ZKP_PENALTY_MS, 3);
  rec_key("pin"); rec_i32(SAFETY_PIN);
  rec_key("d12"); rec_u32(d12_high ? 1 : 0);
  rec_key("n_cfg"); rec_u32(cfg_count);
  rec_send();
}

static void report_cmd(const char *cmd, uint32_t t_us, bool prev) {
  rec_begin("cmd", t_us);
  rec_str("cmd", cmd);
  rec_key("attack"); rec_u32(attack_mode_active ? 1 : 0);
  rec_key("prev"); rec_u32(prev ? 1 : 0);
  rec_key("cycle"); rec_i32(cycle_count);
  rec_send();
}

static void report_err(const char *code, uint32_t t_us, unsigned len) {
  rec_begin("err", t_us);
  rec_str("code", code);
  rec_key("len"); rec_u32(len);
  rec_send();
}

static void report_out(int level, uint32_t t_us) {
  rec_begin("out", t_us);
  rec_key("pin"); rec_i32(SAFETY_PIN);
  rec_key("level"); rec_i32(level);
  rec_key("cycle"); rec_i32(cycle_count);
  rec_key("trust"); rec_fixed(trust_score, 4);
  rec_send();
}

static void report_cfg(uint32_t t_us) {
  rec_begin("cfg", t_us);
  rec_safe_str("algo", current_algo);
  rec_str("wl", workload_name());
  rec_key("alpha"); rec_fixed(ewma_alpha, 4);
  rec_key("trust"); rec_fixed(trust_score, 4);
  rec_key("cycle"); rec_i32(cycle_count);
  rec_key("attack"); rec_u32(attack_mode_active ? 1 : 0);
  rec_key("d12"); rec_u32(d12_high ? 1 : 0);
  rec_key("n_cfg"); rec_u32(cfg_count);
  rec_send();
}

static void report_update(uint32_t t0_us, uint32_t t_us, float exec_time_ms, float obs) {
  rec_begin("upd", t_us);
  rec_key("t0_us"); rec_u32(t0_us);
  rec_key("cycle"); rec_i32(cycle_count);
  rec_key("exec_ms"); rec_fixed(exec_time_ms, 3);
  rec_key("obs"); rec_fixed(obs, 4);
  rec_key("trust"); rec_fixed(trust_score, 4);
  rec_key("attack"); rec_u32(attack_mode_active ? 1 : 0);
  rec_key("below"); rec_u32(trust_score < EVICTION_THRESHOLD ? 1 : 0);
  rec_key("d12"); rec_u32(d12_high ? 1 : 0);
  rec_key("pw_us"); rec_i32(last_write_us);
  last_write_us = (int32_t)rec_send();
  if (out_low_pending) {
    out_low_pending = false;
    report_out(0, out_low_t_us);
  }
}

// The template's threshold branch plus transition bookkeeping. digitalWrite(LOW) is still
// issued on every below-threshold update, exactly as before.
static void threshold_output() {
  if (trust_score < EVICTION_THRESHOLD) {
    uint32_t t_out = micros();
    digitalWrite(SAFETY_PIN, LOW); // Trigger Category 2 Halt
    if (d12_high) {
      d12_high = false;
      out_low_pending = true;
      out_low_t_us = t_out;
    }
  }
}

// Configuration handling shared by setup() and loop(): same state changes as the template.
static void apply_config(JsonDocument &doc, uint32_t t_us) {
  current_algo = doc["algo"].as<String>();
  ewma_alpha = doc["alpha"].as<float>();
  trust_score = 100.0;
  cycle_count = 0;
  attack_mode_active = false;

  // Set memory pointers based on chosen algorithm (unchanged: other names keep the
  // previous workload selection, which the cfg record's "wl" field makes visible)
  if (current_algo == "ZKP") {
    is_zkp_active = true;
    is_ecc_active = false;
  } else if (current_algo == "ECC") {
    is_zkp_active = false;
    is_ecc_active = true;
  } else if (current_algo == "CLOUD") {
    is_zkp_active = false;
    is_ecc_active = false;
  }

  // Re-energize the physical safeguard loop to allow motion
  uint32_t t_high = micros();
  digitalWrite(SAFETY_PIN, HIGH);
  bool changed = !d12_high;
  d12_high = true;
  out_low_pending = false;
  cfg_count++;
  // Records are emitted in device-time order: cfg (processed at t_us) before out (t_high).
  report_cfg(t_us);
  if (changed) report_out(1, t_high);
}

void setup() {
  Serial.begin(115200);
  pinMode(SAFETY_PIN, OUTPUT);
  digitalWrite(SAFETY_PIN, HIGH); // Start in active state to prevent reset jitter (unchanged)
  d12_high = true;

  // Enable DWT Cycle Counter hardware register
  ARM_DEMCR |= ARM_DEMCR_TRCENA;
  ARM_DWT_CTRL |= ARM_DWT_CTRL_CYCCNTENA;

  uECC_set_rng(&RNG);

  // Wait for serial connection
  while (!Serial) {
    ;
  }
  report_identity("boot");

  // --- DYNAMIC SERIAL CONFIGURATION HANDSHAKE ---
  // Block until the Pi Supervisor sends the configuration payload
  bool configured = false;
  uint32_t last_hello = micros();
  while (!configured) {
    if (micros() - last_hello >= 1000000UL) {
      report_identity("hello");
      last_hello = micros();
    }
    if (Serial.available() > 0) {
      String payload = Serial.readStringUntil('\n');
      payload.trim();
      uint32_t t_rx = micros();

      if (payload.startsWith("{") && payload.endsWith("}")) {
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, payload);

        if (!error && doc.containsKey("algo") && doc.containsKey("alpha")) {
          apply_config(doc, t_rx);
          configured = true;
        } else {
          report_err(error ? "bad_json" : "bad_cfg", t_rx, payload.length());
        }
      } else if (payload.length() > 0) {
        report_err("unknown_cmd", t_rx, payload.length());
      }
    }
  }
}

// ------------------------------------------------------------------------------
// Cryptographic Blocks (workload, observation and EWMA code unchanged)
// ------------------------------------------------------------------------------

void execute_ecc_verification() {
  uint8_t private_key[uECC_BYTES];
  uint8_t public_key[uECC_BYTES * 2];

  uint32_t t0_us = micros();                 // V8: outside the DWT-timed region
  ARM_DWT_CYCCNT = 0;
  uint32_t start_cycles = ARM_DWT_CYCCNT;

  // Base ECC Payload (1 loop = ~111.5ms on Cortex-M4)
  uECC_make_key(public_key, private_key);

  uint32_t end_cycles = ARM_DWT_CYCCNT;
  float exec_time_ms = (float)(end_cycles - start_cycles) / 64000.0;

  float current_trust = 100.0;

  if (attack_mode_active) {
    // Immediate trust failure when network attack is active (simulates dropped packets without blocking thread)
    current_trust = 0.0;
  } else {
    // Calibrated Threshold: 150.0ms (gives ~38ms of hardware jitter headroom)
    if (exec_time_ms > ECC_PENALTY_MS) {
      float penalty = (float)(exec_time_ms - ECC_PENALTY_MS);
      current_trust = max(0.0f, 100.0f - penalty);
    }
  }

  trust_score = (ewma_alpha * current_trust) + ((1.0 - ewma_alpha) * trust_score);
  uint32_t t_upd_us = micros();              // V8: trust update time

  threshold_output();
  report_update(t0_us, t_upd_us, exec_time_ms, current_trust);

  cycle_count++;
  delay(10);
}

void execute_zkp_verification() {
  uint8_t private_key[uECC_BYTES];
  uint8_t public_key[uECC_BYTES * 2];

  uint32_t t0_us = micros();                 // V8: outside the DWT-timed region
  ARM_DWT_CYCCNT = 0;
  uint32_t start_cycles = ARM_DWT_CYCCNT;

  // Real ZKP proxy: two secp256r1 scalar multiplications over a static nonzero payload.
  static uint8_t attributes[64];
  static bool payload_init = false;
  if (!payload_init) {
    RNG(attributes, 64);
    attributes[0] |= 1;
    attributes[32] |= 1;
    payload_init = true;
  }

  volatile int acc = 0;
  acc += uECC_compute_public_key(&attributes[0],  public_key);
  acc += public_key[0];
  acc += uECC_compute_public_key(&attributes[32], public_key);
  acc += public_key[0];

  uint32_t end_cycles = ARM_DWT_CYCCNT;
  float exec_time_ms = (float)(end_cycles - start_cycles) / 64000.0;

  float current_trust = 100.0;

  if (attack_mode_active) {
    // Immediate trust failure when network attack is active (simulates dropped packets without blocking thread)
    current_trust = 0.0;
  } else {
    // Original Threshold: 400.0ms (gives ~175 ms headroom vs real 225ms workload)
    if (exec_time_ms > ZKP_PENALTY_MS) {
      float penalty = (float)(exec_time_ms - ZKP_PENALTY_MS);
      current_trust = max(0.0f, 100.0f - penalty);
    }
  }

  trust_score = (ewma_alpha * current_trust) + ((1.0 - ewma_alpha) * trust_score);
  uint32_t t_upd_us = micros();              // V8: trust update time

  threshold_output();
  report_update(t0_us, t_upd_us, exec_time_ms, current_trust);

  cycle_count++;
  delay(10);
}

// ------------------------------------------------------------------------------
// Main Loop
// ------------------------------------------------------------------------------
String input_buffer = "";

void loop() {
  // 1. Listen for commands from the Pi Supervisor (NON-BLOCKING, between cycles)
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      input_buffer.trim();
      uint32_t t_cmd = micros();

      if (input_buffer == "ATTACK") {
        bool prev = attack_mode_active;
        attack_mode_active = true;
        report_cmd("ATTACK", t_cmd, prev);
      } else if (input_buffer == "RECOVER") {
        bool prev = attack_mode_active;
        attack_mode_active = false;
        report_cmd("RECOVER", t_cmd, prev);
      } else if (input_buffer.startsWith("{") && input_buffer.endsWith("}")) {
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, input_buffer);
        if (!error && doc.containsKey("algo") && doc.containsKey("alpha")) {
          // Reset the entire state machine!
          apply_config(doc, t_cmd);
        } else {
          report_err(error ? "bad_json" : "bad_cfg", t_cmd, input_buffer.length());
        }
      } else if (input_buffer.length() > 0) {
        report_err("unknown_cmd", t_cmd, input_buffer.length());
      }

      input_buffer = ""; // Clear buffer for next command
    } else {
      input_buffer += c;
      if (input_buffer.length() > 200) {
        report_err("overflow", micros(), input_buffer.length());
        input_buffer = "";
      }
    }
  }

  // 2. Continuous Mathematical Verification & Safety Watchdog
  if (is_zkp_active) {
    execute_zkp_verification();
  } else if (is_ecc_active) {
    execute_ecc_verification();
  } else if (micros() - last_idle_us >= 1000000UL) {
    last_idle_us = micros();
    rec_begin("idle", last_idle_us);
    rec_safe_str("algo", current_algo);
    rec_send();
  }
}
