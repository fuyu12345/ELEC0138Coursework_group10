
import rsa, base64, time, requests, json

owner = "67AD80ABF1306619992B33C2C96FA574"
uuid = "uuid-" + str(int(time.time()))
timestamp = str(int(time.time()))
message = f"{owner}|{uuid}|{timestamp}"

# Generate keypair (simulate a new device)
(pubkey, privkey) = rsa.newkeys(2048)

signature = base64.b64encode(rsa.sign(message.encode(), privkey, 'SHA-256')).decode()
public_key_str = pubkey.save_pkcs1().decode()

# Step 1: Register new device
print("\n[Step 1] Submitting new device registration...")
register_resp = requests.post("http://127.0.0.1:8080/handshake", json={
    "owner": owner,
    "uuid": uuid,
    "timestamp": timestamp,
    "signature": signature,
    "public_key": public_key_str
})

print("[Register] Status:", register_resp.status_code)
print("[Register] Response:", register_resp.text)

try:
    token = register_resp.json().get("verify_token")
    if token:
        print("\n[Step 2] Simulating email verification using token...")
        print("[Token] -->", token)
        verify_resp = requests.post("http://127.0.0.1:8080/verify_email", json={
            "owner": owner,
            "uuid": uuid,
            "token": token
        })
        print("[Verify] Status:", verify_resp.status_code)
        print("[Verify] Response:", verify_resp.text)
    else:
        print("\n[!] No token returned. Device may already be registered or rejected.")
except Exception as e:
    print("[!] Failed to parse token or send verification:", str(e))
