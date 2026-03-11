from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aendere-diesen-schluessel-unbedingt')

UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        owner TEXT NOT NULL,
        shared INTEGER DEFAULT 0,
        size INTEGER DEFAULT 0,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # Standardbenutzer erstellen (Passwörter bitte ändern!)
    users = [
        ('benutzer1', 'passwort1'),
        ('benutzer2', 'passwort2'),
        ('benutzer3', 'passwort3'),
        ('benutzer4', 'passwort4'),
        ('benutzer5', 'passwort5'),
    ]
    for username, password in users:
        existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if not existing:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                      (username, generate_password_hash(password)))
    db.commit()
    db.close()

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        flash('Falscher Benutzername oder Passwort')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    my_files = db.execute('SELECT * FROM files WHERE owner = ? ORDER BY uploaded_at DESC', (session['user'],)).fetchall()
    shared_files = db.execute('SELECT * FROM files WHERE shared = 1 AND owner != ? ORDER BY uploaded_at DESC', (session['user'],)).fetchall()
    db.close()
    return render_template('dashboard.html', my_files=my_files, shared_files=shared_files, user=session['user'])

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    if 'file' not in request.files:
        flash('Keine Datei ausgewählt')
        return redirect(url_for('dashboard'))
    file = request.files['file']
    shared = 1 if request.form.get('shared') == 'on' else 0
    if file.filename == '':
        flash('Keine Datei ausgewählt')
        return redirect(url_for('dashboard'))
    if file:
        original_name = file.filename
        ext = os.path.splitext(secure_filename(original_name))[1]
        unique_name = str(uuid.uuid4()) + ext
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(filepath)
        size = os.path.getsize(filepath)
        db = get_db()
        db.execute('INSERT INTO files (filename, original_name, owner, shared, size) VALUES (?, ?, ?, ?, ?)',
                  (unique_name, original_name, session['user'], shared, size))
        db.commit()
        db.close()
        flash('Datei erfolgreich hochgeladen!')
    return redirect(url_for('dashboard'))

@app.route('/download/<int:file_id>')
def download(file_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    file = db.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
    db.close()
    if not file:
        flash('Datei nicht gefunden')
        return redirect(url_for('dashboard'))
    if file['owner'] != session['user'] and not file['shared']:
        flash('Keine Berechtigung')
        return redirect(url_for('dashboard'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], file['filename'], as_attachment=True, download_name=file['original_name'])

@app.route('/toggle_share/<int:file_id>')
def toggle_share(file_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    file = db.execute('SELECT * FROM files WHERE id = ? AND owner = ?', (file_id, session['user'])).fetchone()
    if file:
        new_shared = 0 if file['shared'] else 1
        db.execute('UPDATE files SET shared = ? WHERE id = ?', (new_shared, file_id))
        db.commit()
    db.close()
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:file_id>')
def delete(file_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    file = db.execute('SELECT * FROM files WHERE id = ? AND owner = ?', (file_id, session['user'])).fetchone()
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        db.execute('DELETE FROM files WHERE id = ?', (file_id,))
        db.commit()
        flash('Datei gelöscht')
    db.close()
    return redirect(url_for('dashboard'))

def format_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size/(1024*1024):.1f} MB"
    return f"{size/(1024*1024*1024):.1f} GB"

app.jinja_env.filters['format_size'] = format_size

if __name__ == '__main__':
    init_db()
    app.run(debug=False)

with app.app_context():
    init_db()
