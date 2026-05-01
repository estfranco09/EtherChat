#!/usr/bin/env python3
"""
EtherChat - Two-Way Chat
Both terminals run this same script.
One runs as "Terminal 1" (MAC 01), the other as "Terminal 2" (MAC 02).
Each can send and receive simultaneously using threads.

Usage:
  Terminal 1:  sudo python3 chat.py 1
  Terminal 2:  sudo python3 chat.py 2
"""

import socket
import struct
import time
import sys
import threading
from datetime import datetime

# ─── Protocol Constants ───────────────────────────────────────────────────────
ETHERTYPE  = 0x88B5
INTERFACE  = "lo"
MSG_TYPE_CHAT = 0x01

# Each terminal has its own MAC so we can tell messages apart
MACS = {
    "1": b'\x00\x00\x00\x00\x00\x01',
    "2": b'\x00\x00\x00\x00\x00\x02',
}
NAMES = {
    "1": "Terminal 1",
    "2": "Terminal 2",
}
DST_MAC = b'\xff\xff\xff\xff\xff\xff'  # Broadcast

def parse_mac(mac_bytes):
    return ":".join(f"{b:02x}" for b in mac_bytes)

def build_frame(src_mac, message):
    timestamp  = struct.pack("!d", time.time())
    msg_bytes  = message.encode("utf-8")
    payload    = bytes([MSG_TYPE_CHAT]) + timestamp + msg_bytes
    ethertype  = struct.pack("!H", ETHERTYPE)
    return DST_MAC + src_mac + ethertype + payload

def parse_frame(raw, my_mac):
    if len(raw) < 15:
        return None
    src_mac   = raw[6:12]
    ethertype = struct.unpack("!H", raw[12:14])[0]

    # Only accept EtherChat frames NOT from ourselves
    if ethertype != ETHERTYPE:
        return None
    if src_mac == my_mac:
        return None  # ignore our own broadcasts

    payload = raw[14:]
    if len(payload) < 9:
        return None
    if payload[0] != MSG_TYPE_CHAT:
        return None

    timestamp = struct.unpack("!d", payload[1:9])[0]
    message   = payload[9:].decode("utf-8", errors="replace")
    return parse_mac(src_mac), timestamp, message


def receiver_thread(sock, my_mac, peer_name):
    """Runs in background — prints incoming messages."""
    seen = set()  # track (src_mac, timestamp) to deduplicate loopback echoes
    while True:
        try:
            raw, _ = sock.recvfrom(65535)
            result = parse_frame(raw, my_mac)
            if result:
                key = (result[0], result[1])  # (src_mac_str, timestamp)
                if key in seen:
                    continue
                seen.add(key)
                if len(seen) > 200:  # keep memory tidy
                    seen.pop()
                src_mac, timestamp, message = result
                latency = (time.time() - timestamp) * 1000
                # Move to new line so incoming message doesn't collide with input prompt
                print(f"\r\033[K", end="")  # clear current input line
                print(f"  ┌─ {peer_name} ────────────────────────────────")
                print(f"  │  Latency: {latency:.2f} ms  |  Frame: {14+1+8+len(message.encode())} bytes")
                print(f"  └▶ {message}")
                print(f"You ▶ ", end="", flush=True)  # reprint prompt
        except Exception:
            break


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("1", "2"):
        print("Usage: sudo python3 chat.py 1   (or 2 for the other terminal)")
        sys.exit(1)

    my_id    = sys.argv[1]
    peer_id  = "2" if my_id == "1" else "1"
    my_mac   = MACS[my_id]
    my_name  = NAMES[my_id]
    peer_name = NAMES[peer_id]

    print("╔══════════════════════════════════════════════╗")
    print(f"║   EtherChat  ·  {my_name}  ·  Two-Way      ║")
    print("║   Raw Ethernet frames · No IP · Loopback    ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"You are: {my_name}  (MAC: {parse_mac(my_mac)})")
    print(f"Waiting for messages from {peer_name}...")
    print("Type a message and hit Enter to send. Type 'quit' to exit.\n")

    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        sock.bind((INTERFACE, 0))
    except PermissionError:
        print("[ERROR] Run with sudo: sudo python3 chat.py 1")
        sys.exit(1)

    # Start background thread to listen for incoming messages
    t = threading.Thread(target=receiver_thread, args=(sock, my_mac, peer_name), daemon=True)
    t.start()

    # Main thread handles sending
    try:
        while True:
            try:
                message = input("You ▶ ")
            except EOFError:
                break

            if message.strip().lower() == "quit":
                print("Goodbye!")
                break
            if not message.strip():
                continue

            frame = build_frame(my_mac, message)
            sock.send(frame)
            print(f"  ↑ Sent  [{len(frame)} bytes]\n")

    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
