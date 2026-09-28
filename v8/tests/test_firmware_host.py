"""Run the real trust-monitor sketches on the host with a virtual clock (needs g++).

What this establishes (software-only):
1. The V8 sketch emits records that the V8 host parser accepts, with continuous sequence
   numbers and monotonic device time, and with the intended event semantics.
2. EQUIVALENCE: for identical serial input and workload timing, the V8 sketch and the
   historical template (firmware/unified_trust_monitor_template) produce identical trust
   values (bit-for-bit floats), cycle numbers, attack flags and D12 writes at identical
   virtual times. The instrumentation does not change the trust algorithm or output logic.
3. The template's own output parses with the host's legacy-protocol parser.

What it does NOT establish: real workload durations, USB timing, electrical behaviour, or
anything about the flashed binary. uECC and the DWT counter are mocked; the only source
change for the host build redirects the three DWT register-address macros to variables.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FW_V8 = os.path.join(REPO, "firmware", "trust_monitor_v8", "trust_monitor_v8.ino")
FW_TEMPLATE = os.path.join(REPO, "firmware", "unified_trust_monitor_template", "unified_trust_monitor_template.ino")
HARNESS = os.path.join(HERE, "firmware_host")

from onedge_v8 import protocol as P  # noqa: E402

DWT_PATCHES = [
    (r"#define ARM_DWT_CYCCNT\s+\(\*\(volatile uint32_t \*\)0xE0001004\)", "#define ARM_DWT_CYCCNT HOST_DWT_CYCCNT"),
    (r"#define ARM_DWT_CTRL\s+\(\*\(volatile uint32_t \*\)0xE0001000\)", "#define ARM_DWT_CTRL HOST_DWT_CTRL"),
    (r"#define ARM_DEMCR\s+\(\*\(volatile uint32_t \*\)0xE000EDFC\)", "#define ARM_DEMCR HOST_DEMCR"),
]


def find_gxx():
    for c in (os.environ.get("ONEDGE_GXX"), shutil.which("g++"), r"C:\msys64\mingw64\bin\g++.exe"):
        if c and os.path.exists(c):
            return c
    return None


def find_arduinojson():
    home = os.path.expanduser("~")
    for c in (os.environ.get("ONEDGE_ARDUINOJSON_SRC"),
              os.path.join(home, "OneDrive", "Documents", "Arduino", "libraries", "ArduinoJson", "src"),
              os.path.join(home, "Documents", "Arduino", "libraries", "ArduinoJson", "src"),
              os.path.join(home, "Arduino", "libraries", "ArduinoJson", "src")):
        if c and os.path.exists(os.path.join(c, "ArduinoJson.h")):
            return c
    return None


GXX = find_gxx()
AJSON = find_arduinojson()


def build(sketch: str, outdir: str, name: str) -> str:
    with open(sketch, "r", encoding="utf-8") as f:
        text = f.read()
    for pat, rep in DWT_PATCHES:
        text, n = re.subn(pat, rep, text)
        assert n == 1, f"DWT macro pattern not found exactly once in {sketch}: {pat}"
    patched = os.path.join(outdir, name + ".ino")
    with open(patched, "w", encoding="utf-8") as f:
        f.write(text)
    exe = os.path.join(outdir, name + (".exe" if os.name == "nt" else ""))
    cmd = [GXX, "-std=gnu++17", "-O1", "-static", "-w",
           "-DARDUINOJSON_ENABLE_ARDUINO_STRING=1", "-DARDUINOJSON_ENABLE_ARDUINO_STREAM=0",
           "-DARDUINOJSON_ENABLE_ARDUINO_PRINT=0", "-DARDUINOJSON_ENABLE_PROGMEM=0",
           f'-DSKETCH_FILE="{name}.ino"', "-I", HARNESS, "-I", outdir, "-I", AJSON,
           os.path.join(HARNESS, "sketch_main.cpp"), os.path.join(HARNESS, "host_runtime.cpp"), "-o", exe]
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(GXX) + os.pathsep + env.get("PATH", "")
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"build failed for {sketch}:\n{r.stderr[-4000:]}")
    return exe


def run(exe, script, duration_us, ecc=111540, zkp=112430, jitter=0, write_cost=0, offset=0, tmp=None,
        micros_cost=0):
    path = os.path.join(tmp, "script.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for t, text in script:
            f.write(f"{t} {text}\n")
    r = subprocess.run([exe, path, str(duration_us), str(ecc), str(zkp), str(jitter), str(write_cost), str(offset),
                        str(micros_cost)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    writes, snaps, pins = [], [], []
    for line in r.stdout.splitlines():
        parts = line.split(" ")
        if parts[0] == "W":
            writes.append((int(parts[1]), bytes.fromhex(parts[2]) if len(parts) > 2 else b""))
        elif parts[0] == "S":
            snaps.append((int(parts[1]), int(parts[2]), parts[3], float(parts[4]), int(parts[5]), int(parts[6])))
        elif parts[0] == "P":
            pins.append((int(parts[1]), int(parts[2]), int(parts[3])))
    return writes, snaps, pins


def device_messages(writes):
    fr = P.LineFramer()
    cont = P.Continuity()
    out = []
    for t, data in writes:
        for fl in fr.feed(data, t, t):
            m = P.parse_line(fl.raw, fl.overflow, fl.terminated)
            events, ann = cont.observe(m)
            out.append((t, m, events, ann))
    return out, cont


@unittest.skipUnless(GXX and AJSON, "g++ or ArduinoJson headers not available")
class FirmwareHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="fwhost_")
        cls.v8 = build(FW_V8, cls.tmp, "v8")
        cls.tpl = build(FW_TEMPLATE, cls.tmp, "template")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    SCRIPT = [
        (1_200_000, '{"algo":"ECC","alpha":0.3}\\n'),
        (3_000_000, "ATTACK\\n"),
        (4_000_000, "RECOVER\\n"),
        (5_000_000, "HELLO\\n"),
        (5_100_000, "{bad json}\\n"),
        (5_200_000, '{"algo":"ECC"}\\n'),
        (5_300_000, "X" * 250 + "\\n"),
        (6_000_000, '{"algo":"ECC","alpha":0.3}\\n'),
    ]

    def test_v8_records_and_semantics(self):
        # micros() costs 3 us here so that device time advances inside a loop iteration, which
        # exposes any record emitted out of device-time order.
        writes, snaps, pins = run(self.v8, self.SCRIPT, 7_000_000, tmp=self.tmp, micros_cost=3)
        msgs, cont = device_messages(writes)
        bad = [(m.status, m.raw) for _, m, _, _ in msgs if not m.ok]
        self.assertEqual(bad, [])
        self.assertEqual(cont.summary()["missing_records"], 0)
        kinds = [m.kind for _, m, _, _ in msgs]
        self.assertEqual(kinds[0], "boot")
        self.assertEqual(msgs[0][1].fields["seq"], 0)
        self.assertEqual([m.fields["seq"] for _, m, _, _ in msgs], list(range(len(msgs))))
        tdev = [a["t_dev_us"] for _, _, _, a in msgs]
        self.assertEqual(tdev, sorted(tdev))                   # record times non-decreasing in seq order
        self.assertEqual(cont.small_backsteps, 0)
        self.assertGreater(len(set(tdev)), len(tdev) // 2)     # and time really advanced between records
        self.assertIn("hello", kinds[:kinds.index("cfg")])
        cfg = next(m for _, m, _, _ in msgs if m.kind == "cfg")
        self.assertEqual((cfg.fields["trust"], cfg.fields["cycle"], cfg.fields["attack"], cfg.fields["d12"],
                          cfg.fields["wl"], cfg.fields["alpha"]), (100.0, 0, 0, 1, "ECC", 0.3))
        # ATTACK processed between cycles; the next update is the first attacked one
        seq_msgs = [m for _, m, _, _ in msgs]
        i_att = next(i for i, m in enumerate(seq_msgs) if m.kind == "cmd" and m.fields["cmd"] == "ATTACK")
        self.assertEqual((seq_msgs[i_att].fields["prev"], seq_msgs[i_att].fields["attack"]), (0, 1))
        prev_upd = [m for m in seq_msgs[:i_att] if m.kind == "upd"][-1]
        after = [m for m in seq_msgs[i_att:] if m.kind == "upd"]
        self.assertEqual(prev_upd.fields["attack"], 0)
        self.assertEqual([u.fields["attack"] for u in after[:4]], [1, 1, 1, 1])
        self.assertEqual([u.fields["trust"] for u in after[:4]], [70.0, 49.0, 34.3, 24.01])
        self.assertEqual([u.fields["below"] for u in after[:4]], [0, 0, 0, 1])
        self.assertEqual([u.fields["d12"] for u in after[:4]], [1, 1, 1, 0])
        self.assertEqual(after[1].fields["cycle"], after[0].fields["cycle"] + 1)
        # the output-low record follows the crossing update and is timed at/after it
        i_cross = seq_msgs.index(after[3])
        out = seq_msgs[i_cross + 1]
        self.assertEqual((out.kind, out.fields["level"], out.fields["cycle"]), ("out", 0, after[3].fields["cycle"]))
        self.assertGreaterEqual(out.fields["t_us"], after[3].fields["t_us"])
        self.assertEqual(sum(1 for m in seq_msgs if m.kind == "out" and m.fields["level"] == 0), 1)
        # RECOVER clears attack mode but does not raise D12 (latched until configuration)
        i_rec = next(i for i, m in enumerate(seq_msgs) if m.kind == "cmd" and m.fields["cmd"] == "RECOVER")
        self.assertEqual((seq_msgs[i_rec].fields["prev"], seq_msgs[i_rec].fields["attack"]), (1, 0))
        rec_upds = [m for m in seq_msgs[i_rec:] if m.kind == "upd"]
        self.assertTrue(all(u.fields["attack"] == 0 and u.fields["obs"] == 100.0 for u in rec_upds[:3]))
        self.assertTrue(any(u.fields["below"] == 0 for u in rec_upds))
        self.assertTrue(all(u.fields["d12"] == 0 for u in rec_upds if u.fields["t_us"] < 6_000_000))
        errs = [m.fields["code"] for m in seq_msgs if m.kind == "err"]
        self.assertEqual(errs[:4], ["unknown_cmd", "bad_json", "bad_cfg", "overflow"])
        # reconfiguration raises D12: 'cfg' (processing time) then 'out' level 1 (write time)
        i_out1 = next(i for i, m in enumerate(seq_msgs) if m.kind == "out" and m.fields["level"] == 1)
        self.assertEqual(seq_msgs[i_out1 - 1].kind, "cfg")
        self.assertEqual(seq_msgs[i_out1 - 1].fields["n_cfg"], 2)
        self.assertGreaterEqual(seq_msgs[i_out1].fields["t_us"], seq_msgs[i_out1 - 1].fields["t_us"])
        # DWT-derived execution time and device-clock loop period
        self.assertAlmostEqual(after[0].fields["exec_ms"], 111.54, places=3)
        periods = [(b.fields["t0_us"] - a.fields["t0_us"]) for a, b in zip(after, after[1:])]
        self.assertTrue(all(121_500 <= p <= 121_700 for p in periods), periods)
        # every below-threshold update still writes LOW (template behaviour)
        lows = [p for p in pins if p[1] == 12 and p[2] == 0]
        self.assertGreaterEqual(len(lows), 2)

    def scenarios(self):
        base = []
        for algo, alpha, t_att, t_rec in (("ECC", 0.1, 2_000_000, 4_000_000), ("ECC", 0.3, 2_121_000, 2_900_000),
                                          ("ECC", 0.5, 2_000_000, 2_150_000), ("ZKP", 0.3, 2_500_000, 3_600_000),
                                          ("ZKP", 0.5, 2_234_500, 2_600_000)):
            base.append([(500_000, f'{{"algo":"{algo}","alpha":{alpha}}}\\n'), (t_att, "ATTACK\\n"),
                         (t_rec, "RECOVER\\n"), (6_000_000, f'{{"algo":"{algo}","alpha":{alpha}}}\\n'),
                         (7_000_000, "ATTACK\\n"), (9_000_000, "RECOVER\\n")])
        flood = [(500_000, '{"algo":"ECC","alpha":0.3}\\n')]
        flood += [(2_000_000 + k * 50_000, "ATTACK\\n") for k in range(20)] + [(3_000_000, "RECOVER\\n")]
        base.append(flood)
        return base

    def test_equivalence_with_template(self):
        for i, script in enumerate(self.scenarios()):
            for jitter in (0, 400):
                with self.subTest(scenario=i, jitter=jitter):
                    _, s_v8, p_v8 = run(self.v8, script, 10_000_000, jitter=jitter, tmp=self.tmp)
                    _, s_tp, p_tp = run(self.tpl, script, 10_000_000, jitter=jitter, tmp=self.tmp)
                    self.assertGreater(len(s_tp), 30)
                    # guard against a vacuous comparison: the attack path must be exercised
                    self.assertTrue(any(s[4] == 1 for s in s_tp), "ATTACK never processed")
                    self.assertTrue(any(s[3] < 100.0 for s in s_tp), "trust never decreased")
                    self.assertTrue(any(p[1] == 12 and p[2] == 0 for p in p_tp), "D12 never written LOW")
                    self.assertEqual(s_v8, s_tp)            # time, cycle, trust bits, attack, D12
                    self.assertEqual(p_v8, p_tp)            # every digitalWrite, same time/level

    def test_template_output_parses_as_legacy(self):
        writes, snaps, _ = run(self.tpl, self.scenarios()[1], 5_000_000, tmp=self.tmp)
        msgs, cont = device_messages(writes)
        kinds = {m.kind for _, m, _, _ in msgs}
        self.assertTrue({"legacy_upd", "legacy_ready"} <= kinds)
        self.assertTrue(all(m.ok for _, m, _, _ in msgs))
        self.assertEqual(cont.summary()["missing_records"], 0)
        trusts = [m.fields["trust"] for _, m, _, _ in msgs if m.kind == "legacy_upd"]
        self.assertIn(24.01, trusts)

    def test_micros_wrap_is_unwrapped(self):
        offset = (1 << 32) - 3_000_000
        writes, _, _ = run(self.v8, self.SCRIPT[:3], 6_000_000, offset=offset, tmp=self.tmp)
        msgs, cont = device_messages(writes)
        self.assertEqual(cont.resets, 0)
        raw = [m.fields["t_us"] for _, m, _, _ in msgs]
        self.assertTrue(any(b < a for a, b in zip(raw, raw[1:])))       # the raw clock did wrap
        ext = [a["t_dev_us"] for _, _, _, a in msgs]
        self.assertEqual(ext, sorted(ext))                               # unwrapped clock is monotonic

    def test_report_write_time_is_measured(self):
        writes, _, _ = run(self.v8, self.SCRIPT[:3], 4_000_000, write_cost=150, tmp=self.tmp)
        msgs, _ = device_messages(writes)
        pw = [m.fields["pw_us"] for _, m, _, _ in msgs if m.kind == "upd"]
        self.assertEqual(pw[0], -1)
        self.assertTrue(all(v == 150 for v in pw[1:]), pw[:5])


if __name__ == "__main__":
    unittest.main()
