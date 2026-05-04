from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import threading
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from seed_data import get_seed_entries

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

_seed_printed = set()  # 출력된 시드 ID 추적 (서버 재시작 시 초기화)

@app.route('/pending', methods=['GET'])
def pending():
    cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

    # 실제 제보 중 가장 오래된 미출력 항목
    conn = get_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute(
        'SELECT * FROM submissions WHERE printed = 0 AND hidden = 0 AND timestamp > %s ORDER BY id ASC LIMIT 1',
        (cutoff,)
    )
    row = c.fetchone()
    conn.close()
    real = dict(row) if row else None

    use_seed = os.environ.get('USE_SEED_DATA', 'false').lower() == 'true'
    if not use_seed:
        if real:
            return jsonify({**real, "type": "real"})
        return jsonify(None)

    # 시드 중 아직 출력 안 된 가장 오래된 항목
    seeds = get_seed_entries()  # 시간순 정렬
    next_seed = next((s for s in seeds if s['id'] not in _seed_printed), None)

    # 둘 중 timestamp가 더 이른 것 반환
    if real and next_seed:
        if real['timestamp'] <= next_seed['timestamp']:
            return jsonify({**real, "type": "real"})
        _seed_printed.add(next_seed['id'])
        return jsonify({**next_seed, "type": "seed"})
    if real:
        return jsonify({**real, "type": "real"})
    if next_seed:
        _seed_printed.add(next_seed['id'])
        return jsonify({**next_seed, "type": "seed"})
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
    public_fields = [{"id": r["id"], "description": r["description"], "country": r["country"],
                      "timestamp": r["timestamp"], "latitude": r["latitude"], "longitude": r["longitude"]}
                     for r in public]
    if os.environ.get('USE_SEED_DATA', 'false').lower() == 'true':
        combined = public_fields + get_seed_entries()
        combined.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
        return jsonify({"auth": False, "data": combined})
    return jsonify({"auth": False, "data": public_fields})

def _auto_hide_worker():
    while True:
        try:
            cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            conn = get_conn()
            c = conn.cursor()
            c.execute("UPDATE submissions SET hidden = 1 WHERE hidden = 0 AND timestamp < %s", (cutoff,))
            conn.commit()
            conn.close()
        except Exception:
            pass
        time.sleep(600)  # 10분마다 실행

threading.Thread(target=_auto_hide_worker, daemon=True).start()

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)