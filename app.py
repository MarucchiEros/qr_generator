from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import re
from sqlalchemy.dialects.postgresql import UUID
import qrcode
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/qr_code_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    qr_codes = db.relationship('QRCode', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

class QRCode(db.Model):
    id = db.Column(db.String(36), primary_key=True)  
    url = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, default=db.func.current_timestamp())
    password = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)

QR_FOLDER = os.path.join(app.root_path, 'static', 'qr_codes')
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)

def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)?'
        r'(([A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
        r'localhost|' 
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
        r'(:\d+)?' 
        r'(\/[^\s]*)?$', re.IGNORECASE)

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
    return redirect(url_for('login_or_register'))

@app.route('/login_or_register', methods=['GET', 'POST'])
def login_or_register():
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form['username']
        password = request.form['password']
        
        if action == 'login':
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect(url_for('generate_qr'))
            else:
                return render_template('login.html', error="Credenziali errate")

        elif action == 'register':
            email = request.form['email']
            hashed_password = generate_password_hash(password)

            user = User(username=username, email=email, password=hashed_password)

            try:
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login_or_register'))
            except Exception as e:
                print(f"Errore durante la registrazione: {e}")
                return render_template('login.html', error="Errore durante la registrazione")

    return render_template('login.html')

@app.route('/generate_qr', methods=['GET', 'POST'])
def generate_qr():
    if 'user_id' not in session:
        return redirect(url_for('login_or_register'))
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        url = request.form['url']
        password = request.form.get('password')

        if url.strip() and is_valid_url(url.strip()):
            qr_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password.strip()) if password else None
            user_id = session.get('user_id')
            try:
                new_qr_code = QRCode(id=qr_id, url=url.strip(), password=hashed_password, user_id=user_id)
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

            img_path = os.path.join(QR_FOLDER, f"{qr_id}.png")
            with open(img_path, 'wb') as f:
                f.write(img_io.getvalue())

            return jsonify({'image': img_io.getvalue().decode('latin1'), 'qr_id': qr_id})

    qr_codes = QRCode.query.filter_by(user_id=user.id).all()

    return render_template('index.html', username=user.username, qr_codes=qr_codes)

@app.route('/my_qr_codes')
def my_qr_codes():
    if 'user_id' not in session:
        return redirect(url_for('login_or_register')) 
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    qr_codes = user.qr_codes 

    return render_template('my_qr_codes.html', qr_codes=qr_codes)

@app.route('/delete_qr_code/<qr_id>', methods=['POST'])
def delete_qr_code(qr_id):
    if 'user_id' not in session:
        return redirect(url_for('login_or_register')) 
    qr_code = QRCode.query.get(qr_id)
    if not qr_code:
        return "QR Code non trovato.", 404

    if qr_code.user_id != session['user_id']:
        return "Non hai i permessi per eliminare questo QR code.", 403

    try:
        db.session.delete(qr_code)
        db.session.commit()

        img_path = os.path.join(QR_FOLDER, f"{qr_id}.png")
        if os.path.exists(img_path):
            os.remove(img_path)
        return redirect(url_for('generate_qr'))  
    except Exception as e:
        print(f"Errore durante l'eliminazione del QR code: {e}")
        return "Errore durante l'eliminazione del QR code.", 500

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
