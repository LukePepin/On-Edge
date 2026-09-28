// Entry point that compiles one trust-monitor sketch for the host (TEST HARNESS ONLY).
// SKETCH_FILE is a copy of the .ino in which only the three DWT register-address macros are
// redirected to host variables (see v8/tests/test_firmware_host.py).
#include <stdio.h>
#include <stdlib.h>

#include "Arduino.h"
#include SKETCH_FILE

extern uint64_t host_ecc_us, host_zkp_mult_us, host_jitter_us, host_write_cost_us, host_poll_cost_us,
    host_micros_offset, host_micros_cost_us;
void host_load_script(const char *path);

int main(int argc, char **argv) {
  if (argc < 3) {
    fprintf(stderr, "usage: %s script duration_us [ecc_us zkp_mult_us jitter_us write_cost_us micros_offset]\n",
            argv[0]);
    return 2;
  }
  host_load_script(argv[1]);
  uint64_t duration = strtoull(argv[2], nullptr, 10);
  if (argc > 3) host_ecc_us = strtoull(argv[3], nullptr, 10);
  if (argc > 4) host_zkp_mult_us = strtoull(argv[4], nullptr, 10);
  if (argc > 5) host_jitter_us = strtoull(argv[5], nullptr, 10);
  if (argc > 6) host_write_cost_us = strtoull(argv[6], nullptr, 10);
  if (argc > 7) host_micros_offset = strtoull(argv[7], nullptr, 10);
  if (argc > 8) host_micros_cost_us = strtoull(argv[8], nullptr, 10);
  setup();
  while (host_now_us < duration) loop();
  printf("END %llu\n", (unsigned long long)host_now_us);
  return 0;
}
