from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder='.')
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'pwou2026')

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id SERIAL PRIMARY KEY,
        description TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        country TEXT,
        timestamp TEXT,
        printed INTEGER DEFAULT 0,
        hidden INTEGER DEFAULT 0
    )""")
    try:
        c.execute("ALTER TABLE submissions ADD COLUMN hidden INTEGER DEFAULT 0")
    except:
        pass
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
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO submissions (description, latitude, longitude, country, timestamp)
                 VALUES (%s, %s, %s, %s, %s)""",
              (data.get('description'), data.get('latitude'), data.get('longitude'),
               data.get('country'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/pending', methods=['GET'])
def pending():
    conn = get_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT * FROM submissions WHERE printed = 0 AND hidden = 0 ORDER BY id ASC LIMIT 1')
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify(None)

@app.route('/mark_printed/<int:submission_id>', methods=['POST'])
def mark_printed(submission_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE submissions SET printed = 1 WHERE id = %s', (submission_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/toggle_hidden/<int:submission_id>', methods=['POST'])
def toggle_hidden(submission_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE submissions SET hidden = CASE WHEN hidden = 1 THEN 0 ELSE 1 END WHERE id = %s', (submission_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    pw = request.args.get('pw', '')
    conn = get_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT * FROM submissions ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    result = [dict(r) for r in rows]
    if pw == ADMIN_PASSWORD:
        return jsonify({"auth": True, "data": result})
    public = [r for r in result if not r.get('hidden')]
    return jsonify({"auth": False, "data": [{"id": r["id"], "description": r["description"], "country": r["country"], "timestamp": r["timestamp"], "latitude": r["latitude"], "longitude": r["longitude"]} for r in public]})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)