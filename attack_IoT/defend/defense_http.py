from flask import Flask, request, jsonify
import rsa, json, base64, time, secrets

from shared import device_registry

app = Flask(__name__)

pending_devices = {}
verification_tokens = {}

@app.route('/handshake', methods=['POST'])
def verify_handshake():
    data = request.json
    owner = data.get("owner")
    uuid = data.get("uuid")
    timestamp = data.get("timestamp")
    signature = data.get("signature")
    public_key = data.get("public_key")

    if not all([owner, uuid, timestamp, signature]):
        return jsonify({"status": "error", "msg": "Missing fields"}), 400

    if owner in device_registry:
        device_list = device_registry[owner]
        match = next((d for d in device_list if d["uuid"] == uuid), None)
        if match:
            message = f"{owner}|{uuid}|{timestamp}"
            if abs(int(time.time()) - int(timestamp)) > 30:
                return jsonify({"status": "error", "msg": "Timestamp expired"}), 403

            try:
                rsa.verify(message.encode(), base64.b64decode(signature), match["pubkey"])
                return jsonify({"status": "ok", "msg": "Verified"}), 200
            except:
                return jsonify({"status": "error", "msg": "Signature verification failed"}), 401

    # New device
    if not public_key:
        return jsonify({"status": "error", "msg": "Unrecognized device. Email verification required."}), 403

    if owner not in pending_devices:
        pending_devices[owner] = []

    if any(dev["uuid"] == uuid for dev in pending_devices[owner]):
        return jsonify({"status": "error", "msg": "Device already submitted. Awaiting email verification."}), 403

    try:
        new_pubkey = rsa.PublicKey.load_pkcs1(public_key.encode())
        token = secrets.token_hex(8)
        pending_devices[owner].append({
            "uuid": uuid,
            "pubkey": new_pubkey
        })
        verification_tokens[(owner, uuid)] = token
        return jsonify({
            "status": "wait",
            "msg": "Pending email verification",
            "verify_token": token
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": f"Invalid public_key format: {str(e)}"}), 400

@app.route('/verify_email', methods=['POST'])
def verify_email():
    data = request.json
    owner = data.get("owner")
    uuid = data.get("uuid")
    token = data.get("token")

    if not owner or not uuid or not token:
        return jsonify({"status": "error", "msg": "Missing fields"}), 400

    expected_token = verification_tokens.get((owner, uuid))
    if token != expected_token:
        return jsonify({"status": "error", "msg": "Invalid token"}), 403

    devices = pending_devices.get(owner, [])
    for device in devices:
        if device["uuid"] == uuid:
            device_registry[owner].append(device)
            devices.remove(device)
            del verification_tokens[(owner, uuid)]
            return jsonify({"status": "ok", "msg": "Device verified and registered"}), 200

    return jsonify({"status": "error", "msg": "Pending device not found"}), 404

if __name__ == '__main__':
    app.run(port=8080)
