from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import requests
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # คีย์ที่ใช้ในการเข้ารหัส session

class CryptoPair:
    def __init__(self, symbol, initial_price):
        self.symbol = symbol
        self.initial_price = initial_price

def get_prices(symbols):
    symbols_param = json.dumps(symbols, separators=(',', ':'))
    url = f'https://api.binance.com/api/v3/ticker/price?symbols={symbols_param}'
    response = requests.get(url)
    data = response.json()
    return {e['symbol']: float(e['price']) for e in data}

def calculate_percentage_change(initial_price, current_price):
    try:
        percentage_change = ((current_price - initial_price) / initial_price) * 100
        return percentage_change
    except ZeroDivisionError:
        return "Initial price cannot be zero."

def save_pairs_to_file(pairs):
    with open('crypto_pairs.json', 'w') as file:
        json.dump([pair.__dict__ for pair in pairs], file)

def load_pairs_from_file():
    pairs = []
    if os.path.exists('crypto_pairs.json'):
        with open('crypto_pairs.json', 'r') as file:
            data = json.load(file)
            for item in data:
                pairs.append(CryptoPair(**item))
    return pairs

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # ตรวจสอบข้อมูลล็อกอิน
        if username == 'Admin' and password == 'Iota7799':  # คุณสามารถเปลี่ยนชื่อผู้ใช้และรหัสผ่านได้ตามต้องการ
            session['logged_in'] = True
            session.permanent = False  # ทำให้ session หมดอายุเมื่อปิดเบราว์เซอร์
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials, please try again.'

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    pairs = load_pairs_from_file()
    pairs_json = json.dumps([pair.__dict__ for pair in pairs])
    return render_template('index.html', pairs_json=pairs_json)

@app.route('/get_crypto_data', methods=['POST'])
def get_crypto_data():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    data = request.json
    symbols = data.get('symbols', [])
    filter_min = data.get('min', None)
    filter_max = data.get('max', None)

    pairs = [CryptoPair(symbol['symbol'], float(symbol['initial_price'])) for symbol in symbols]

    try:
        current_prices = get_prices([pair.symbol for pair in pairs])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    percentage_changes = []
    for pair in pairs:
        current_price = current_prices[pair.symbol]
        percentage_change = calculate_percentage_change(pair.initial_price, current_price)
        if (filter_min is None or percentage_change >= filter_min) and (filter_max is None or percentage_change <= filter_max):
            percentage_changes.append((pair.symbol, percentage_change))

    percentage_changes.sort(key=lambda x: x[1], reverse=True)

    return jsonify(percentage_changes)

@app.route('/settings')
def settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    pairs = load_pairs_from_file()
    return render_template('settings.html', pairs=pairs)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    data = request.json
    pairs = [CryptoPair(pair['symbol'], float(pair['initial_price'])) for pair in data['pairs']]
    save_pairs_to_file(pairs)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
