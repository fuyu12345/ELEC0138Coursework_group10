import rsa
import base64

# Registered email: attacktest321@gmail.com
# OWNER = MD5("attacktest321@gmail.com").upper() = "67AD80ABF1306619992B33C2C96FA574"
# Supports multiple devices per OWNER (uuid + public_key)

device_registry = {
    "67AD80ABF1306619992B33C2C96FA574": [
        {
            "uuid": "attack-uuid-registered-0001",
            "pubkey": rsa.PublicKey.load_pkcs1(open("public.pem", "rb").read())
        }
    ]
}
