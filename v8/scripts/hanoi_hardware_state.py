#!/usr/bin/env python3
"""Read UR hardware state on read-only port 30012; never sends commands.

Packet layout: https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/primary-secondary-guide.html
Lengths include the four-byte length and one-byte type. Unknown packages are skipped.
"""
import argparse
import json
import math
import socket
import struct
import time


def read_hardware_state(host="192.168.0.149", timeout=3.0):
    deadline = time.monotonic() + timeout
    samples = []
    with socket.create_connection((host, 30012), timeout=timeout) as stream:
        def read(count):
            result = bytearray()
            while len(result) < count:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("No advancing complete robot hardware state")
                stream.settimeout(remaining)
                chunk = stream.recv(count - len(result))
                if not chunk:
                    raise RuntimeError("Robot hardware state connection closed")
                result.extend(chunk)
            return bytes(result)

        while len(samples) < 3:
            length = struct.unpack("!I", read(4))[0]
            if not 5 <= length <= 1048576:
                raise ValueError("Invalid hardware packet length")
            packet = read(length - 4)
            if packet[0] != 16:
                continue
            state = {}
            position = 1
            while position < len(packet):
                if len(packet) - position < 5:
                    raise ValueError("Truncated hardware package header")
                size, kind = struct.unpack_from("!IB", packet, position)
                if size < 5 or position + size > len(packet):
                    raise ValueError("Invalid hardware package length")
                data = packet[position + 5:position + size]
                if kind == 0 and len(data) >= 15:
                    state["controller_timestamp_us"] = struct.unpack_from("!Q", data)[0]
                    flags = struct.unpack_from("!7?", data, 8)
                    state.update(zip(("real_robot_connected", "real_robot_enabled", "power_on",
                                      "emergency_stopped", "protective_stopped", "program_running",
                                      "program_paused"), flags))
                elif kind == 1 and len(data) >= 246:
                    state["joint_positions_rad"] = [struct.unpack_from("!d", data, i * 41)[0] for i in range(6)]
                    state["joint_velocities_rad_s"] = [struct.unpack_from("!d", data, i * 41 + 16)[0] for i in range(6)]
                elif kind == 4 and len(data) >= 96:
                    values = list(struct.unpack_from("!12d", data))
                    state["tcp_pose_m_rotvec_rad"] = values[:6]
                    state["active_tcp_offset_m_rotvec_rad"] = values[6:]
                position += size
            arrays = ("joint_positions_rad", "joint_velocities_rad_s", "tcp_pose_m_rotvec_rad", "active_tcp_offset_m_rotvec_rad")
            if "controller_timestamp_us" in state and all(key in state for key in arrays):
                if not all(math.isfinite(value) for key in arrays for value in state[key]):
                    raise ValueError("Nonfinite hardware state")
                samples.append(state)
    if any(b["controller_timestamp_us"] <= a["controller_timestamp_us"] for a, b in zip(samples, samples[1:])):
        raise RuntimeError("Robot hardware timestamp is not advancing")
    result = samples[-1]
    result["source"] = "direct_robot_read_only_secondary_30012"
    result["advancing_controller_timestamp"] = True
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="192.168.0.149")
    args = parser.parse_args()
    print(json.dumps(read_hardware_state(args.host), allow_nan=False))
