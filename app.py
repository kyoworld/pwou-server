from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import random
import threading
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from seed_data import get_random_seed_entry

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
    conn.commit()

    try:
        c.execute("ALTER TABLE submissions ADD COLUMN hidden INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        conn.rollback()

    c.execute("""CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY,
        description TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        country TEXT,
        timestamp TEXT,
        printed INTEGER DEFAULT 0,
        hidden INTEGER DEFAULT 0
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
    ts = data.get('timestamp') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO submissions (description, latitude, longitude, country, timestamp)
                 VALUES (%s, %s, %s, %s, %s)""",
              (data.get('description'), data.get('latitude'), data.get('longitude'),
               data.get('country'), ts))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/pending', methods=['GET'])
def pending():
    cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute(
        'SELECT * FROM submissions WHERE printed = 0 AND hidden = 0 AND timestamp > %s ORDER BY id ASC LIMIT 1',
        (cutoff,)
    )
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({**dict(row), "type": "real"})
    return jsonify(None)

@app.route('/flush_expired', methods=['POST'])
def flush_expired():
    cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE submissions SET printed = 1 WHERE printed = 0 AND timestamp < %s",
        (cutoff,)
    )
    affected = c.rowcount
    conn.commit()
    conn.close()
    return jsonify({"flushed": affected})

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
    if pw == ADMIN_PASSWORD:
        c.execute('SELECT * FROM submissions ORDER BY id DESC')
    else:
        c.execute('SELECT * FROM submissions WHERE hidden = 0 ORDER BY id DESC LIMIT 20')
    rows = c.fetchall()
    conn.close()
    result = [dict(r) for r in rows]
    if pw == ADMIN_PASSWORD:
        return jsonify({"auth": True, "data": result})
    public_fields = [{"id": r["id"], "description": r["description"], "country": r["country"],
                      "timestamp": r["timestamp"], "latitude": r["latitude"], "longitude": r["longitude"]}
                     for r in result]
    return jsonify({"auth": False, "data": public_fields})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM archive')
    total_archived = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM submissions')
    total_active = c.fetchone()[0]
    conn.close()
    return jsonify({"total_archived": total_archived, "total_active": total_active})

@app.route('/api/board', methods=['GET'])
def get_board():
    conn = get_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute(
        'SELECT id, description, country, timestamp, latitude, longitude'
        ' FROM submissions WHERE hidden = 0 ORDER BY id DESC LIMIT 100'
    )
    rows = c.fetchall()
    conn.close()
    return jsonify({"data": [dict(r) for r in rows]})

_SEED_INTERVALS = [10, 20, 30, 60]

def _seed_insert_worker():
    print("[SEED] worker started")
    while True:
        time.sleep(random.choice(_SEED_INTERVALS))
        if os.environ.get('USE_SEED_DATA', 'false').lower() != 'true':
            continue
        try:
            entry = get_random_seed_entry()
            conn = get_conn()
            c = conn.cursor()
            c.execute(
                "INSERT INTO submissions (description, latitude, longitude, country, timestamp, printed) VALUES (%s, %s, %s, %s, %s, 0)",
                (entry["description"], entry["latitude"], entry["longitude"], entry["country"], entry["timestamp"])
            )
            conn.commit()
            conn.close()
            print(f"[SEED] inserted: {entry['country']} {entry['timestamp']}")
        except Exception as e:
            print(f"[SEED] insert error: {e}")

def _cleanup_worker():
    while True:
        try:
            cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            conn = get_conn()
            c = conn.cursor()
            c.execute("""
                INSERT INTO archive (id, description, latitude, longitude, country, timestamp, printed, hidden)
                SELECT id, description, latitude, longitude, country, timestamp, printed, hidden
                FROM submissions WHERE timestamp < %s
                ON CONFLICT (id) DO NOTHING
            """, (cutoff,))
            c.execute("DELETE FROM submissions WHERE timestamp < %s", (cutoff,))
            conn.commit()
            conn.close()
        except Exception:
            pass
        time.sleep(600)  # 10분마다 실행

threading.Thread(target=_seed_insert_worker, daemon=True).start()
threading.Thread(target=_cleanup_worker, daemon=True).start()

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)