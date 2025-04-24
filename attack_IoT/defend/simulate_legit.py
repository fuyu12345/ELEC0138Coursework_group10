
import rsa, base64, time, requests

owner = "67AD80ABF1306619992B33C2C96FA574"
uuid = "attack-uuid-registered-0001"
timestamp = str(int(time.time()))
message = f"{owner}|{uuid}|{timestamp}"

priv = rsa.PrivateKey.load_pkcs1(open("private.pem", "rb").read())
sig = base64.b64encode(rsa.sign(message.encode(), priv, 'SHA-256')).decode()

resp = requests.post("http://127.0.0.1:8080/handshake", json={
    "owner": owner,
    "uuid": uuid,
    "timestamp": timestamp,
    "signature": sig
})

print(resp.status_code, resp.text)
