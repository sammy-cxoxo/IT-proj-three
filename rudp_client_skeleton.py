#!/usr/bin/env python3
"""
rudp_client_skeleton.py — STUDENT SKELETON
Goal: Implement a minimal "Reliable UDP" (RUDP) client over UDP (stop-and-wait).

YOU MUST IMPLEMENT:
  1) 3-way handshake:  (you send) SYN -> (expect) SYN-ACK -> (you send) ACK
  2) DATA send loop (stop-and-wait):
       - split MESSAGE into CHUNK-sized pieces (seq: 0,1,2,...)
       - for each chunk: send DATA, wait for DATA-ACK with matching seq
       - if timeout or wrong ACK: retransmit (retry up to RETRIES)
  3) Teardown: (you send) FIN -> (expect) FIN-ACK

Use Wireshark with: udp.port == <your_assigned_port>
"""
import socket, struct, time


# ===================== CONFIG (EDIT HOST/PORT) =====================
SERVER_HOST = '127.0.0.1'   # server IP or hostname
ASSIGNED_PORT = 30018       # <-- REPLACE with your assigned UDP port
SERVER = (SERVER_HOST, ASSIGNED_PORT)
# ==================================================================

# Timing/reliability parameters
RTO = 0.5        # retransmission timeout (seconds)
RETRIES = 10      # max retries per send
CHUNK = 200      # bytes per DATA chunk

# --- Protocol type codes (1 byte) ---
SYN, SYN_ACK, ACK, DATA, DATA_ACK, FIN, FIN_ACK = 1,2,3,4,5,6,7

# Header format: type(1B) | seq(4B) | len(2B)
HDR = '!B I H'
HDR_SZ = struct.calcsize(HDR)

# A larger message to force multiple DATA/ACK pairs.
MESSAGE = (
    'Hello from student RUDP client!\n'
    'This demo asks you to implement handshake, DATA+ACK with stop-and-wait, '
    'and FIN teardown.\n'
    'Below are numbered lines to create many packets.\n'
    + 'Line ' + '\nLine '.join(str(i) for i in range(1, 101)) + '\n'
)

def pack_msg(tp: int, seq: int, payload: bytes = b'') -> bytes:
    if isinstance(payload, str):
        payload = payload.encode()
    return struct.pack(HDR, tp, seq, len(payload)) + payload

def unpack_msg(pkt: bytes):
    if len(pkt) < HDR_SZ:
        return None, None, b''
    tp, seq, ln = struct.unpack(HDR, pkt[:HDR_SZ])
    return tp, seq, pkt[HDR_SZ:HDR_SZ+ln]

def send_recv_with_retry(sock, pkt, expect_types, expect_seq=None):
    """
    Utility: send a packet and wait (with timeout) for a response
    whose type is in 'expect_types' and optionally has matching seq.
    Retries up to RETRIES times.
    Returns (tp, seq) on success, (None, None) on failure.
    """
    cur_to = RTO
    for _ in range(RETRIES):
        sock.sendto(pkt, SERVER)
        sock.settimeout(cur_to)
        try:
            resp, _ = sock.recvfrom(2048)
            tp, s, _ = unpack_msg(resp)
            if tp in expect_types and (expect_seq is None or s == expect_seq):
                return tp, s
        except socket.timeout:
            pass
        cur_to = min(cur_to * 1.5, 2.5)
    return None, None

def main():
    cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ============ PHASE 1: HANDSHAKE (YOU IMPLEMENT) ==============
    print('[CLIENT] SYN')
    syn_pkt = pack_msg(SYN, 0, b'')
    tp, _ = send_recv_with_retry(cli, syn_pkt, expect_types={SYN_ACK})
    if tp != SYN_ACK:
        print('[CLIENT] Handshake failed: no SYN-ACK')
        cli.close()
        return

    print('[CLIENT] SYN-ACK')
    cli.sendto(pack_msg(ACK, 0, b''), SERVER)
    print('[CLIENT] Connection established')
    # ===============================================================

    # ============ PHASE 2: DATA SEND LOOP (YOU IMPLEMENT) =========
    data_bytes = MESSAGE if isinstance(MESSAGE, (bytes, bytearray)) else str(MESSAGE).encode()
    seq = 0

    for off in range(0, len(data_bytes), CHUNK):
        chunk = data_bytes[off:off + CHUNK]
        print(f'[CLIENT] DATA seq={seq} len={len(chunk)}')

        data_pkt = pack_msg(DATA, seq, chunk)
        tp, got_seq = send_recv_with_retry(cli, data_pkt, expect_types={DATA_ACK}, expect_seq=seq)
        if tp != DATA_ACK or got_seq != seq:
            print(f'[CLIENT] Failed to get DATA-ACK for seq={seq} after {RETRIES} retries')
            cli.close()
            return

        print(f'[CLIENT] ACK seq={seq}')
        seq += 1
    # ===============================================================

    # ============ PHASE 3: TEARDOWN (YOU IMPLEMENT) ===============
    # TODO:
    #   - print('[CLIENT] FIN')
    #   - send FIN and wait (with retry) for FIN-ACK
    #   - on success print('[CLIENT] Connection closed')
    pass  # <-- replace with your teardown code
    # ===============================================================

    cli.close()

if __name__ == '__main__':
    main()
