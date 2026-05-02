from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder='.')
CORS(app)

DB_PATH = "submissions.db"
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'pwou2026')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        country TEXT,
        timestamp TEXT,
        printed INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/board')
def board():
    return send_from_directory('.', 'board.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO submissions (description, latitude, longitude, country, timestamp)
                 VALUES (?, ?, ?, ?, ?)""",
              (data.get('description'), data.get('latitude'), data.get('longitude'),
               data.get('country'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/pending', methods=['GET'])
def pending():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM submissions WHERE printed = 0 ORDER BY id ASC LIMIT 1')
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({"id": row[0], "description": row[1], "latitude": row[2], "longitude": row[3], "country": row[4], "timestamp": row[5]})
    return jsonify(None)

@app.route('/mark_printed/<int:submission_id>', methods=['POST'])
def mark_printed(submission_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE submissions SET printed = 1 WHERE id = ?', (submission_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    pw = request.args.get('pw', '')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM submissions ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    result = [{"id": r[0], "description": r[1], "latitude": r[2], "longitude": r[3], "country": r[4], "timestamp": r[5], "printed": r[6]} for r in rows]
    if pw == ADMIN_PASSWORD:
        return jsonify({"auth": True, "data": result})
    return jsonify({"auth": False, "data": [{"id": r["id"], "description": r["description"], "country": r["country"], "timestamp": r["timestamp"]} for r in result]})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)