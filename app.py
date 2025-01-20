from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
import os
from io import BytesIO
import uuid
import re

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/qr_code_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class QRCode(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    url = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, default=db.func.current_timestamp())
    password = db.Column(db.String(255), nullable=True)

QR_FOLDER = os.path.join(app.root_path, 'static', 'qr_codes')
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' 
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

@app.before_request
def test_db_connection():
    try:
        db.engine.connect()
        print("Connessione al database riuscita!")
    except Exception as e:
        print(f"Errore nella connessione al database: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    url = request.form['url']
    password = request.form.get('password')

    if url.strip() and is_valid_url(url.strip()):
        qr_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password.strip()) if password else None
        try:
            new_qr_code = QRCode(id=qr_id, url=url.strip(), password=hashed_password)
            db.session.add(new_qr_code)
            db.session.commit() 
            print("QR code inserito correttamente") 
        except Exception as e:
            print(f"Errore durante l'inserimento nel database: {e}") 
            db.session.rollback()
            return jsonify({'error': 'Errore nel salvataggio del QR code'}), 500

        pinggy_url = f"{request.scheme}://{request.host}/validate/{qr_id}"

        img = qrcode.make(pinggy_url)
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return jsonify({'image': img_io.getvalue().decode('latin1'), 'qr_id': qr_id})

    return jsonify({'error': 'URL non valido'}), 400

@app.route('/validate/<qr_id>', methods=['GET', 'POST'])
def validate_qr(qr_id):
    qr_info = QRCode.query.get(qr_id)

    if not qr_info:
        return "QR Code non valido o scaduto.", 404

    if qr_info.password is None:
        return redirect(qr_info.url)

    if request.method == 'POST':
        password = request.form.get('password')
        if check_password_hash(qr_info.password, password):
            return redirect(qr_info.url)
        else:
            return render_template('validate.html', qr_id=qr_id, error="Password errata. Riprova.")

    return render_template('validate.html', qr_id=qr_id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=8000)
