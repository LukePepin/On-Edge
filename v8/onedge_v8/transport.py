"""Byte transports to the trust monitor: real serial (pyserial) and simulated.

The DeviceLink is the only user of a transport. Transports never discard received bytes;
read() returns whatever arrived (possibly partial lines, possibly several lines).
"""
from __future__ import annotations

import glob
import os
import sys


class TransportError(IOError):
    """The port is unavailable or disconnected."""


class SerialTransport:
    simulated = False

    def __init__(self, port: str = "auto", baud: int = 115200, read_timeout_s: float = 0.02,
                 by_id_pattern: str = "*Arduino*Nano_33_BLE*"):
        self.requested_port = port
        self.baud = baud
        self.read_timeout_s = read_timeout_s
        self.by_id_pattern = by_id_pattern
        self.port = None
        self._ser = None

    @property
    def description(self) -> str:
        return f"serial {self.port or self.requested_port} @ {self.baud}"

    def resolve_port(self) -> str:
        if self.requested_port and self.requested_port != "auto":
            return self.requested_port
        # "auto" only succeeds when exactly one candidate exists: with several boards attached
        # (e.g. the monitor and another Nano) picking one would silently record the wrong device.
        if sys.platform.startswith("linux"):
            candidates = sorted(glob.glob(os.path.join("/dev/serial/by-id", self.by_id_pattern)))
            if not candidates:
                candidates = [p for p in sorted(glob.glob("/dev/ttyACM*")) if os.path.exists(p)]
        else:
            candidates = []
            try:
                from serial.tools import list_ports
                candidates = sorted(info.device for info in list_ports.comports()
                                    if (info.vid, info.pid) == (0x2341, 0x805A))   # Arduino Nano 33 BLE
            except ImportError:
                pass
        return select_single_port(candidates)

    def open(self):
        try:
            import serial  # pyserial
        except ImportError as exc:
            raise TransportError("pyserial is not installed") from exc
        port = self.resolve_port()
        users = port_users(port)
        if users:
            raise TransportError(f"{port} is already open by PID(s) {users}: stop the other process first "
                                 "(the V8 daemon must be the only owner of the monitor's serial port)")
        try:
            self._ser = serial.Serial(port, self.baud, timeout=self.read_timeout_s, write_timeout=1.0,
                                      exclusive=True if os.name == "posix" else None)
        except (serial.SerialException, OSError, ValueError) as exc:
            raise TransportError(f"cannot open {port}: {exc}") from exc
        self.port = port

    def read(self, max_bytes: int = 4096) -> bytes:
        if self._ser is None:
            raise TransportError("port not open")
        try:
            waiting = self._ser.in_waiting
            return self._ser.read(min(max_bytes, max(1, waiting)))
        except Exception as exc:   # pyserial raises SerialException / OSError on unplug
            raise TransportError(f"read failed: {exc}") from exc

    def write(self, data: bytes):
        if self._ser is None:
            raise TransportError("port not open")
        try:
            self._ser.write(data)
            self._ser.flush()
        except Exception as exc:
            raise TransportError(f"write failed: {exc}") from exc

    def close(self):
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None


def select_single_port(candidates: list) -> str:
    """The one auto-detected port, or TransportError when there are none or several."""
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise TransportError("no trust-monitor serial port found (set serial.port explicitly)")
    raise TransportError("several candidate serial ports found; set serial.port to the trust monitor's "
                         "/dev/serial/by-id path: " + ", ".join(candidates))


def port_users(port: str) -> list:
    """PIDs (other than ours) holding the tty open, found via /proc on Linux. Read-only."""
    if not sys.platform.startswith("linux"):
        return []
    try:
        target = os.path.realpath(port)
    except OSError:
        return []
    pids = []
    for fd_dir in glob.glob("/proc/[0-9]*/fd"):
        pid = int(fd_dir.split("/")[2])
        if pid == os.getpid():
            continue
        try:
            for fd in os.listdir(fd_dir):
                try:
                    if os.path.realpath(os.path.join(fd_dir, fd)) == target:
                        pids.append(pid)
                        break
                except OSError:
                    continue
        except OSError:
            continue
    return pids
