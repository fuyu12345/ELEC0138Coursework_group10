import socket, json, base64, rsa, time
from shared import device_registry

BUFFER_SIZE = 1024
UDP_PORT = 20002

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))
print("[INFO] UDP defense server started")

while True:
    data, addr = sock.recvfrom(BUFFER_SIZE)
    sender_ip = addr[0]

    try:
        payload = json.loads(data[16:].decode())
        result = payload["result"]
        owner = result["owner"]
        uuid = result["uuid"]
        timestamp = result["timestamp"]
        signature = result["signature"]

        if owner not in device_registry:
            print(f"[ALERT] Unknown OWNER from {sender_ip}")
            continue

        match = next((d for d in device_registry[owner] if d["uuid"] == uuid), None)
        if not match:
            print(f"[ALERT] UUID not recognized for {owner} from {sender_ip}")
            continue

        if abs(int(time.time()) - int(timestamp)) > 30:
            print(f"[ALERT] Timestamp expired from {sender_ip}")
            continue

        message = f"{owner}|{uuid}|{timestamp}"
        try:
            rsa.verify(message.encode(), base64.b64decode(signature), match["pubkey"])
            print(f"[OK] Valid device from {owner} ({uuid}) @ {sender_ip}")
        except:
            print(f"[ALERT] Signature invalid for {owner} ({uuid}) from {sender_ip}")
    except Exception as e:
        print(f"[ERROR] Malformed UDP packet from {sender_ip}: {e}")
