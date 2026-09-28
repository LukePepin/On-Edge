import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onedge_v8 import protocol as P  # noqa: E402


def upd(seq, t, cycle=0, trust=100.0, attack=0, below=0, d12=1, t0=None, obs=100.0, exec_ms=111.5):
    t0 = t - 111500 if t0 is None else t0
    return (f'{{"ev":"upd","seq":{seq},"t_us":{t},"t0_us":{t0 % (1 << 32)},"cycle":{cycle},"exec_ms":{exec_ms},'
            f'"obs":{obs},"trust":{trust},"attack":{attack},"below":{below},"d12":{d12},"pw_us":120}}').encode()


class FramerTests(unittest.TestCase):
    def test_partial_line_across_reads(self):
        fr = P.LineFramer()
        line = upd(1, 1000)
        out = fr.feed(line[:10], 1, 11)
        self.assertEqual(out, [])
        out = fr.feed(line[10:30], 2, 12)
        self.assertEqual(out, [])
        out = fr.feed(line[30:] + b"\r\n", 3, 13)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].raw, line)
        self.assertEqual(out[0].first_rx_mono_ns, 1)
        self.assertEqual(out[0].rx_mono_ns, 3)
        self.assertTrue(P.parse_line(out[0].raw).ok)

    def test_multiple_lines_in_one_read(self):
        fr = P.LineFramer()
        data = upd(1, 1000) + b"\r\n" + upd(2, 2000) + b"\n" + upd(3, 3000)[:5]
        out = fr.feed(data, 5, 15)
        self.assertEqual([P.parse_line(x.raw).fields["seq"] for x in out], [1, 2])
        self.assertEqual(fr.pending_bytes(), 5)

    def test_overflow_is_reported_not_dropped(self):
        fr = P.LineFramer(max_line_bytes=50)
        out = fr.feed(b"x" * 80, 1, 1)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].overflow)
        out = fr.feed(b"yyy\n" + upd(4, 4000)[:40] + b"\n", 2, 2)
        self.assertTrue(out[0].overflow)                # tail of the oversized line
        self.assertEqual(P.parse_line(out[0].raw, out[0].overflow).status, P.OVERFLOW)
        self.assertFalse(out[1].overflow)
        self.assertEqual(P.parse_line(out[1].raw).status, P.NOT_JSON_OBJECT)

    def test_unterminated_fragment_flushed_on_disconnect(self):
        fr = P.LineFramer()
        fr.feed(b'{"ev":"upd","seq"', 1, 1)
        frag = fr.flush_partial(2, 2)
        self.assertFalse(frag.terminated)
        self.assertEqual(P.parse_line(frag.raw, terminated=False).status, P.UNTERMINATED)
        self.assertIsNone(fr.flush_partial(3, 3))


class ParseTests(unittest.TestCase):
    def test_valid_records(self):
        self.assertEqual(P.parse_line(upd(7, 12345)).kind, "upd")
        m = P.parse_line(b'{"ev":"cmd","seq":8,"t_us":13000,"cmd":"ATTACK","attack":1,"prev":0,"cycle":3}')
        self.assertTrue(m.ok)
        self.assertEqual(m.fields["cmd"], "ATTACK")
        m = P.parse_line(b'{"ev":"cfg","seq":0,"t_us":5,"status":"READY","algo":"ECC","wl":"ECC","alpha":0.3,'
                         b'"trust":100.0,"cycle":0,"attack":0,"d12":1,"n_cfg":1}')
        self.assertTrue(m.ok, m.problems)

    def test_malformed_and_invalid(self):
        self.assertEqual(P.parse_line(b'{"ev":"upd","seq":1,').status, P.NOT_JSON_OBJECT)
        self.assertEqual(P.parse_line(b'{"ev":"upd","seq":1,}').status, P.MALFORMED_JSON)
        self.assertEqual(P.parse_line(b'{"ev":"upd","seq":1,"t_us":5}').status, P.INVALID_FIELDS)
        self.assertEqual(P.parse_line(b'{"ev":"zzz","seq":1,"t_us":5}').status, P.UNKNOWN_MESSAGE)
        self.assertEqual(P.parse_line(b'\xff\xfe{"ev":1}').status, P.INVALID_ENCODING)
        self.assertEqual(P.parse_line(b"   ").status, P.EMPTY)
        self.assertEqual(P.parse_line(b"garbage").status, P.NOT_JSON_OBJECT)
        self.assertEqual(P.parse_line(upd(1, 5, trust=130.0)).status, P.INVALID_VALUE)
        self.assertEqual(P.parse_line(upd(1, 5).replace(b'"attack":0', b'"attack":2')).status, P.INVALID_FIELDS)
        # NaN printed by an Arduino float print is not valid JSON
        self.assertEqual(P.parse_line(upd(1, 5).replace(b'"trust":100.0', b'"trust":nan')).status,
                         P.MALFORMED_JSON)

    def test_legacy_protocol(self):
        m = P.parse_line(b'{"cycle": 12, "exec_time_ms": 111.54, "trust_score": 70.00}')
        self.assertEqual((m.kind, m.status, m.protocol), ("legacy_upd", P.OK, "legacy"))
        self.assertEqual(m.fields["trust"], 70.0)
        self.assertIsNone(m.seq)
        self.assertEqual(P.parse_line(b'{"status": "READY"}').kind, "legacy_ready")


class ContinuityTests(unittest.TestCase):
    def feed(self, c, lines):
        out = []
        for ln in lines:
            ev, ann = c.observe(P.parse_line(ln))
            out.append((ev, ann))
        return out

    def test_gap_detection(self):
        c = P.Continuity()
        res = self.feed(c, [upd(10, 1000), upd(11, 2000), upd(14, 3000)])
        self.assertEqual(res[2][0][0].kind, "gap")
        self.assertEqual(res[2][0][0].detail["missing"], 2)
        self.assertEqual(c.missing_total, 2)

    def test_boot_starts_new_epoch(self):
        c = P.Continuity()
        boot = b'{"ev":"boot","seq":0,"t_us":900,"fw":"trust_monitor_v8","ver":"8.0.0","proto":1}'
        res = self.feed(c, [upd(50, 5_000_000), upd(51, 5_100_000), boot, upd(1, 1000)])
        self.assertEqual(res[2][0][0].kind, "reset")
        self.assertEqual(res[3][1]["epoch"], 1)
        self.assertEqual(c.resets, 1)

    def test_sequence_regression_is_reset(self):
        c = P.Continuity()
        res = self.feed(c, [upd(50, 5_000_000), upd(3, 5_100_000)])
        self.assertEqual(res[1][0][0].kind, "reset")
        self.assertEqual(res[1][1]["epoch"], 1)

    def test_duplicate(self):
        c = P.Continuity()
        res = self.feed(c, [upd(5, 1000), upd(6, 2000), upd(6, 2000)])
        self.assertEqual(res[2][0][0].kind, "duplicate")

    def test_32bit_clock_wrap_unwraps(self):
        c = P.Continuity()
        near = (1 << 32) - 50_000
        res = self.feed(c, [upd(1, near, t0=near - 111_500), upd(2, 70_000, t0=(70_000 - 111_500))])
        t1, t2 = res[0][1]["t_dev_us"], res[1][1]["t_dev_us"]
        self.assertEqual(t2 - t1, 120_000)
        self.assertEqual(res[1][1]["epoch"], 0)
        self.assertEqual(res[1][1]["t0_dev_us"], t2 - 111_500)

    def test_clock_backstep_is_reset(self):
        c = P.Continuity()
        res = self.feed(c, [upd(1, 10_000_000), upd(2, 3_000_000)])
        kinds = [e.kind for e in res[1][0]]
        self.assertIn("clock_backstep", kinds)
        self.assertEqual(res[1][1]["epoch"], 1)

    def test_small_backstep_is_not_a_reset(self):
        c = P.Continuity()
        res = self.feed(c, [upd(1, 10_000_000), upd(2, 9_999_900), upd(3, 10_100_000)])
        self.assertEqual(c.resets, 0)
        self.assertEqual(c.small_backsteps, 1)
        self.assertEqual(res[1][1]["t_dev_us"], 9_999_900)

    def test_legacy_cycle_gap(self):
        c = P.Continuity()
        lines = [b'{"status": "READY"}'] + [
            f'{{"cycle": {i}, "exec_time_ms": 111.5, "trust_score": 100.00}}'.encode() for i in (0, 1, 3)]
        res = self.feed(c, lines)
        self.assertEqual(res[3][0][0].kind, "legacy_cycle_gap")
        self.assertEqual(res[3][0][0].detail["missing"], 1)



class PortSelectionTests(unittest.TestCase):
    def test_auto_requires_exactly_one_candidate(self):
        from onedge_v8.transport import TransportError, select_single_port
        self.assertEqual(select_single_port(["/dev/serial/by-id/a"]), "/dev/serial/by-id/a")
        with self.assertRaises(TransportError):
            select_single_port([])
        with self.assertRaises(TransportError) as ctx:
            select_single_port(["/dev/serial/by-id/a", "/dev/serial/by-id/b"])
        self.assertIn("/dev/serial/by-id/b", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
