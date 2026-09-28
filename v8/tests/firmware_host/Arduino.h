// Host-side mock of the Arduino API used by the trust-monitor sketches.
// TEST HARNESS ONLY: virtual time, scripted serial input, captured serial output and pin
// writes. Used by v8/tests/test_firmware_host.py to run the real .ino logic on a PC.
#pragma once

#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <string>

typedef bool boolean;
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1

// ---- virtual time and DWT emulation -------------------------------------------------
extern uint64_t host_now_us;
extern volatile uint32_t HOST_DWT_CYCCNT;
extern volatile uint32_t HOST_DWT_CTRL;
extern volatile uint32_t HOST_DEMCR;
void host_advance_us(uint64_t us);

unsigned long micros();
unsigned long millis();
void delay(unsigned long ms);
void pinMode(int pin, int mode);
void digitalWrite(int pin, int level);

template <class T>
T max(T a, T b) { return a > b ? a : b; }

// ---- String ----------------------------------------------------------------------------
class String {
 public:
  String() {}
  String(const char *s) { if (s) s_ = s; }
  String(const String &o) : s_(o.s_) {}
  String &operator=(const String &o) { s_ = o.s_; return *this; }
  String &operator=(const char *s) { if (s) s_ = s; else s_.clear(); return *this; }
  const char *c_str() const { return s_.c_str(); }
  unsigned int length() const { return (unsigned int)s_.size(); }
  bool concat(const char *s) { if (s) s_ += s; return true; }
  bool startsWith(const char *p) const { return s_.compare(0, strlen(p), p) == 0; }
  bool endsWith(const char *p) const {
    size_t n = strlen(p);
    return s_.size() >= n && s_.compare(s_.size() - n, n, p) == 0;
  }
  void trim() {
    const char *ws = " \t\r\n\v\f";
    size_t b = s_.find_first_not_of(ws);
    if (b == std::string::npos) { s_.clear(); return; }
    size_t e = s_.find_last_not_of(ws);
    s_ = s_.substr(b, e - b + 1);
  }
  char charAt(unsigned int i) const { return i < s_.size() ? s_[i] : 0; }
  String &operator+=(char c) { s_ += c; return *this; }
  bool operator==(const char *o) const { return s_ == o; }
  bool operator==(const String &o) const { return s_ == o.s_; }

 private:
  std::string s_;
};

// ---- Serial ----------------------------------------------------------------------------
class HostSerial {
 public:
  void begin(long) {}
  explicit operator bool() const { return true; }
  int available();
  int read();
  size_t write(const uint8_t *buf, size_t n);
  size_t write(uint8_t c) { return write(&c, 1); }
  size_t print(const char *s);
  size_t print(int v);
  size_t print(unsigned int v);
  size_t print(long v);
  size_t print(unsigned long v);
  size_t print(double v, int digits = 2);
  size_t println(const char *s);
  String readStringUntil(char terminator);
};
extern HostSerial Serial;
