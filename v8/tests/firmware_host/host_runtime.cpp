// Virtual-time runtime for running trust-monitor sketches on a PC (TEST HARNESS ONLY).
//
// Output lines (stdout):
//   W <t_us> <hex>                          bytes passed to one Serial write/print call
//   S <t_us> <cycle> <trust_bits> <trust> <attack> <pin12>   state at each trust report line
//   P <t_us> <pin> <level>                  every digitalWrite call
//   END <t_us>
// Time only advances through workloads (uECC mocks), delay(), serial polling and the
// optional per-write cost, so identical inputs give identical timelines.
#include <stdio.h>
#include <string.h>

#include <deque>
#include <string>

#include "Arduino.h"
#include "uECC.h"

uint64_t host_now_us = 0;
volatile uint32_t HOST_DWT_CYCCNT = 0;
volatile uint32_t HOST_DWT_CTRL = 0;
volatile uint32_t HOST_DEMCR = 0;
HostSerial Serial;

uint64_t host_ecc_us = 111540;       // ECC key generation duration (virtual)
uint64_t host_zkp_mult_us = 112430;  // one scalar multiplication (two per ZKP-proxy cycle)
uint64_t host_jitter_us = 0;         // +/- deterministic jitter per workload call
uint64_t host_write_cost_us = 0;     // virtual duration of one Serial write/print call
uint64_t host_poll_cost_us = 1;      // virtual time consumed by a poll that finds no input
uint64_t host_micros_offset = 0;     // added to micros() to exercise the 32-bit wrap
uint64_t host_micros_cost_us = 0;    // virtual time consumed by each micros() call (ordering tests)

extern float trust_score;
extern int cycle_count;
extern bool attack_mode_active;

struct Input {
  uint64_t t;
  std::string bytes;
};
static std::deque<Input> script;
static std::deque<uint8_t> rx;
static std::string line;
static int pin12 = -1;
static uint32_t lcg = 12345u;

static void deliver() {
  while (!script.empty() && script.front().t <= host_now_us) {
    for (char c : script.front().bytes) rx.push_back((uint8_t)c);
    script.pop_front();
  }
}

void host_advance_us(uint64_t us) {
  host_now_us += us;
  HOST_DWT_CYCCNT += (uint32_t)(us * 64u);   // 64 MHz core clock
  deliver();
}

static uint64_t jittered(uint64_t base) {
  if (!host_jitter_us) return base;
  lcg = lcg * 1664525u + 1013904223u;
  int64_t j = (int64_t)(lcg % (2 * host_jitter_us + 1)) - (int64_t)host_jitter_us;
  return (uint64_t)((int64_t)base + j);
}

unsigned long micros() {
  unsigned long t = (unsigned long)((host_now_us + host_micros_offset) & 0xFFFFFFFFull);
  if (host_micros_cost_us) host_advance_us(host_micros_cost_us);
  return t;
}
unsigned long millis() { return (unsigned long)(((host_now_us + host_micros_offset) / 1000u) & 0xFFFFFFFFull); }
void delay(unsigned long ms) { host_advance_us((uint64_t)ms * 1000u); }
void pinMode(int, int) {}
void digitalWrite(int pin, int level) {
  printf("P %llu %d %d\n", (unsigned long long)host_now_us, pin, level);
  if (pin == 12) pin12 = level;
}

void uECC_set_rng(uECC_RNG_Function) {}
int uECC_make_key(uint8_t *, uint8_t *) { host_advance_us(jittered(host_ecc_us)); return 1; }
int uECC_compute_public_key(const uint8_t *priv, uint8_t *pub) {
  host_advance_us(jittered(host_zkp_mult_us));
  pub[0] = priv[0];
  return 1;
}

int HostSerial::available() {
  deliver();
  if (rx.empty()) host_advance_us(host_poll_cost_us);
  return (int)rx.size();
}

int HostSerial::read() {
  if (rx.empty()) return -1;
  int c = rx.front();
  rx.pop_front();
  return c;
}

static void on_output(const char *data, size_t n) {
  printf("W %llu ", (unsigned long long)host_now_us);
  for (size_t i = 0; i < n; i++) printf("%02x", (unsigned char)data[i]);
  printf("\n");
  for (size_t i = 0; i < n; i++) {
    line.push_back(data[i]);
    if (data[i] == '\n') {
      if (line.find("\"ev\":\"upd\"") != std::string::npos || line.find("\"trust_score\"") != std::string::npos) {
        uint32_t bits;
        memcpy(&bits, &trust_score, sizeof(bits));
        printf("S %llu %d %08x %.9g %d %d\n", (unsigned long long)host_now_us, cycle_count, bits,
               (double)trust_score, attack_mode_active ? 1 : 0, pin12);
      }
      line.clear();
    }
  }
  if (host_write_cost_us) host_advance_us(host_write_cost_us);
}

size_t HostSerial::write(const uint8_t *buf, size_t n) { on_output((const char *)buf, n); return n; }
size_t HostSerial::print(const char *s) { on_output(s, strlen(s)); return strlen(s); }
size_t HostSerial::println(const char *s) {
  std::string t = std::string(s) + "\r\n";
  on_output(t.c_str(), t.size());
  return t.size();
}
size_t HostSerial::print(int v) { char b[16]; int n = snprintf(b, sizeof b, "%d", v); on_output(b, n); return n; }
size_t HostSerial::print(unsigned int v) { char b[16]; int n = snprintf(b, sizeof b, "%u", v); on_output(b, n); return n; }
size_t HostSerial::print(long v) { char b[24]; int n = snprintf(b, sizeof b, "%ld", v); on_output(b, n); return n; }
size_t HostSerial::print(unsigned long v) { char b[24]; int n = snprintf(b, sizeof b, "%lu", v); on_output(b, n); return n; }

// Arduino Print::printFloat algorithm (ArduinoCore-API), so legacy output is byte-identical.
size_t HostSerial::print(double number, int digits) {
  std::string out;
  if (isnan(number)) out = "nan";
  else if (isinf(number)) out = "inf";
  else if (number > 4294967040.0 || number < -4294967040.0) out = "ovf";
  else {
    if (number < 0.0) { out += '-'; number = -number; }
    double rounding = 0.5;
    for (int i = 0; i < digits; ++i) rounding /= 10.0;
    number += rounding;
    unsigned long int_part = (unsigned long)number;
    double remainder = number - (double)int_part;
    out += std::to_string(int_part);
    if (digits > 0) out += '.';
    while (digits-- > 0) {
      remainder *= 10.0;
      unsigned int d = (unsigned int)remainder;
      out += std::to_string(d);
      remainder -= d;
    }
  }
  on_output(out.c_str(), out.size());
  return out.size();
}

String HostSerial::readStringUntil(char terminator) {   // Stream timeout: 1000 ms
  String s;
  while (true) {
    uint64_t start = host_now_us;
    while (rx.empty() && host_now_us - start < 1000000u) host_advance_us(host_poll_cost_us ? host_poll_cost_us : 1);
    if (rx.empty()) break;
    char c = (char)rx.front();
    rx.pop_front();
    if (c == terminator) break;
    s += c;
  }
  return s;
}

// Script lines: "<t_us> <text>" where the text may contain \n, \r and \\ escapes.
void host_load_script(const char *path) {
  FILE *f = fopen(path, "rb");
  if (!f) { fprintf(stderr, "cannot open script %s\n", path); exit(2); }
  char buf[4096];
  while (fgets(buf, sizeof buf, f)) {
    char *sp = strchr(buf, ' ');
    if (!sp) continue;
    *sp = 0;
    Input in;
    in.t = strtoull(buf, nullptr, 10);
    for (char *p = sp + 1; *p && *p != '\n' && *p != '\r'; p++) {
      if (*p == '\\' && p[1]) {
        p++;
        in.bytes.push_back(*p == 'n' ? '\n' : *p == 'r' ? '\r' : *p);
      } else {
        in.bytes.push_back(*p);
      }
    }
    script.push_back(in);
  }
  fclose(f);
}
