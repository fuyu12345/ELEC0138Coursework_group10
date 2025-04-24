# Security and Privacy Assessment of a Sales Management System (SMS)

This project presents a comprehensive **security and privacy assessment** of a web-based **Sales Management System (SMS)** tailored for enterprise environments. The system supports business-critical functions such as **transaction processing**, **inventory management**, and **machine learning-powered analytics**. Furthermore, the SMS integrates **IoT components** via a shared wireless network to enable real-time environmental monitoring and automation.

While these features enhance operational efficiency, they also increase the **attack surface** of the system. This repository contains implementations of several simulated attacks and defense strategies to explore and mitigate potential vulnerabilities.

---

## 🗂 Project Structure

This project is organized into the following folders:

### 📁 `attack_datapoision`
Contains scripts related to **data poisoning attacks**, targeting the machine learning components of the SMS.

- `poison.py`: Simulates data poisoning scenarios.
- `fuzzy_key.py`: Generates fuzzy identifiers for malicious data injection.

---

### 📁 `attack_IoT`
Includes **attack and defense** implementations for the IoT subsystem integrated into SMS.

- IoT-side network penetration and spoofing attack scripts.
- Defense mechanisms to detect and counteract adversarial behaviors.

---

### 📁 `attack_phishing`
Implements **phishing attack simulations** and corresponding countermeasures.

- Code for creating fake login pages.
- Defense logic to identify and block phishing attempts.

---


### 📁 `website`
This folder contains the **Flask-based web application** we built to simulate various attacks.

#### 🔌 Key File:
- `src/route.py`: Contains the route definitions for the Flask application.

The website has already been modified to include **defense strategies** described in the final report. These strategies are directly integrated into the application logic to demonstrate secure practices in a real-world simulation environment.

---

## ⚙️ Setup Instructions (Windows)

### 🔧 Create and Activate a Virtual Environment

Open your terminal in the root project directory and run the following commands:

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

## 📦 Install Dependencies

Install all the packages from the `requirements.txt` file by running the following command in the terminal:

```bash
pip install -r requirements.txt
```




then if you want to activate the website, run the flask app

add the following lines in the terminal
```bash
flask --app src run --debug
```
