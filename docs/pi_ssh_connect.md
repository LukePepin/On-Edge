# Connecting to the Edge Supervisor Pi over SSH

The bench/robot supervisor described in the [README](../README.md) runs on a Raspberry Pi 4
(ROS 2 Humble), reachable on the home network as `on-edge-pi.local`.

## Prerequisites

- Windows OpenSSH client (built into Windows 10/11 — `ssh` should already work from
  PowerShell with no install).
- The Pi and your computer on the same local network.
- The Pi's login password (not stored here — see note below).

## 1. Check the Pi is reachable

```powershell
ping on-edge-pi.local
```

If this times out, the Pi is likely powered off or on a different network/VLAN. mDNS
(`.local`) resolution requires both machines to be on the same LAN segment.

## 2. Connect

```powershell
ssh seeker@on-edge-pi.local
```

- First time connecting from a new machine, you'll get a host key fingerprint prompt —
  type `yes` to trust it.
- You'll then be prompted for the password. Typing is invisible (no characters or
  cursor movement shown) — that's normal terminal behavior, not a stuck prompt.

## 3. Verify you're actually on the Pi

```bash
hostname
uname -a
```

Expect `on-edge-pi` and a Linux/aarch64 kernel string. If you see your Windows machine's
name instead, the SSH session didn't actually open.

## 4. Disconnect

```bash
exit
```

## Optional: passwordless login (SSH key)

Typing the password every time gets old for repeated bench sessions. To set up key-based
auth instead:

```powershell
ssh-keygen -t ed25519 -C "on-edge-pi access"
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh seeker@on-edge-pi.local "cat >> ~/.ssh/authorized_keys"
```

After this, `ssh seeker@on-edge-pi.local` should connect without a password prompt.

## Note on credentials

The Pi's login password is intentionally **not** written down in this file or committed
anywhere in this repo. Keep it in a password manager, not in project docs.
