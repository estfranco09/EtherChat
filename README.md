EtherChat 🖧
A two-way chat application that communicates using raw Ethernet frames — no IP addresses, no TCP, no UDP. Pure Layer 2 networking.
Built as a final project for a Computer Networks course, running on a single Ubuntu 24.04 Azure VM with two terminal sessions simulating separate machines.

How It Works
Most chat apps use TCP/IP. EtherChat skips all of that and talks directly at the Data Link Layer (Layer 2) using custom Ethernet frames with a handcrafted protocol:
FieldSizeDescriptionDestination MAC6 bytesff:ff:ff:ff:ff:ff (broadcast)Source MAC6 bytes00:00:00:00:00:01 or :02EtherType2 bytes0x88B5 (custom experimental)MSG_TYPE1 byte0x01 = chat messageTimestamp8 bytesUnix time as IEEE 754 doubleMessageVariableUTF-8 encoded text
Each terminal runs the same script with a different ID (1 or 2). A background thread listens for incoming frames while the main thread handles sending — enabling real-time two-way communication.

Requirements

Linux (Ubuntu recommended)
Python 3
sudo access (required for raw socket access)
Two terminal windows on the same machine

No third-party libraries needed — only Python standard library.

Setup & Usage
1. Clone the repo
bashgit clone https://github.com/estfranco09/EtherChat.git
cd EtherChat
2. Open two terminal windows on the same Linux machine
3. In Terminal 2, start first:
bashsudo python3 chat.py 2
4. In Terminal 1:
bashsudo python3 chat.py 1
5. Start chatting!
Type a message in either terminal and press Enter. It will appear instantly on the other side with latency and frame size info displayed.
Type quit to exit.

Example Output
Terminal 1:
You ▶ Hello from Layer 2!
  ↑ Sent  [37 bytes]

  ┌─ Terminal 2 ─────────────────────────────
  │  Latency: 0.17 ms  |  Frame: 30 bytes
  └▶ Hey back!
Terminal 2:
  ┌─ Terminal 1 ─────────────────────────────
  │  Latency: 0.23 ms  |  Frame: 37 bytes
  └▶ Hello from Layer 2!

You ▶ Hey back!
  ↑ Sent  [30 bytes]

Optional: Capture Raw Frames
To see the raw Ethernet frames as they travel through the loopback interface, open a third terminal and run:
bashsudo tcpdump -i lo -XX ether proto 0x88b5

Project Info

Course: Computer Networks
VM: Microsoft Azure — Ubuntu 24.04 (Standard B2ats v2)
Interface: Linux loopback (lo)
Language: Python 3 (standard library only)
