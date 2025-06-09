import json
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import uuid
import hashlib
import os

DB_PATH = 'db.sqlite'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, '..', 'frontend', 'index.html')

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Create tables
cur.execute('''CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT,
  birth_date TEXT,
  phone TEXT,
  username TEXT,
  email TEXT UNIQUE,
  password TEXT,
  role TEXT DEFAULT 'candidate',
  approved INTEGER DEFAULT 0
)''')
cur.execute('''CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  datetime TEXT,
  category TEXT,
  points INTEGER,
  description TEXT
)''')
cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  event_id INTEGER,
  attended INTEGER,
  UNIQUE(user_id, event_id)
)''')
cur.execute('''CREATE TABLE IF NOT EXISTS tokens (
  token TEXT PRIMARY KEY,
  user_id INTEGER
)''')
conn.commit()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user_id: int) -> str:
    token = uuid.uuid4().hex
    cur.execute('INSERT INTO tokens(token, user_id) VALUES (?, ?)', (token, user_id))
    conn.commit()
    return token


def get_user_by_token(token: str):
    row = cur.execute('SELECT user_id FROM tokens WHERE token=?', (token,)).fetchone()
    if not row:
        return None
    user = cur.execute('SELECT * FROM users WHERE id=?', (row['user_id'],)).fetchone()
    return user


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({'error': 'invalid json'}, status=400)
            return
        path = urlparse(self.path).path

        if path == '/api/auth/register':
            self.handle_register(data)
        elif path == '/api/auth/login':
            self.handle_login(data)
        elif path == '/api/events':
            self.handle_create_event(data)
        elif path == '/api/attendance':
            self.handle_attendance(data)
        elif path.startswith('/api/roles/'):
            user_id = path.split('/')[-1]
            self.handle_role_update(user_id, data)
        else:
            self._send_json({'error': 'not found'}, status=404)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html'):
            try:
                with open(INDEX_PATH, 'rb') as f:
                    body = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self._send_json({'error': 'not found'}, status=404)
        elif path == '/api/events':
            self.handle_get_events()
        elif path == '/api/users':
            self.handle_get_users()
        else:
            self._send_json({'error': 'not found'}, status=404)

    # Handlers
    def handle_register(self, data):
        try:
            cur.execute('INSERT INTO users(full_name, birth_date, phone, username, email, password) VALUES (?, ?, ?, ?, ?, ?)',
                        (data['full_name'], data['birth_date'], data['phone'], data.get('username'), data['email'], hash_password(data['password'])))
            conn.commit()
            self._send_json({'status': 'ok'})
        except Exception as e:
            self._send_json({'error': str(e)}, status=400)

    def handle_login(self, data):
        user = cur.execute('SELECT * FROM users WHERE email=?', (data['email'],)).fetchone()
        if not user or hash_password(data['password']) != user['password']:
            self._send_json({'error': 'invalid credentials'}, status=400)
            return
        token = create_token(user['id'])
        self._send_json({'token': token})

    def auth_user(self):
        header = self.headers.get('Authorization', '')
        if header.startswith('Bearer '):
            token = header.split(' ')[1]
            return get_user_by_token(token)
        return None

    def handle_get_events(self):
        user = self.auth_user()
        if not user:
            self._send_json({'error': 'unauthorized'}, status=401)
            return
        rows = cur.execute('SELECT * FROM events').fetchall()
        events = [dict(row) for row in rows]
        self._send_json(events)

    def handle_create_event(self, data):
        user = self.auth_user()
        if not user or user['role'] not in ('admin', 'chairman'):
            self._send_json({'error': 'forbidden'}, status=403)
            return
        cur.execute('INSERT INTO events(title, datetime, category, points, description) VALUES (?, ?, ?, ?, ?)',
                    (data['title'], data['datetime'], data['category'], data['points'], data.get('description')))
        conn.commit()
        self._send_json({'status': 'created'})

    def handle_attendance(self, data):
        user = self.auth_user()
        if not user:
            self._send_json({'error': 'unauthorized'}, status=401)
            return
        try:
            cur.execute('INSERT OR REPLACE INTO attendance(user_id, event_id, attended) VALUES (?, ?, ?)',
                        (user['id'], data['event_id'], int(bool(data.get('attended')))))
            conn.commit()
            self._send_json({'status': 'saved'})
        except Exception as e:
            self._send_json({'error': str(e)}, status=400)

    def handle_get_users(self):
        user = self.auth_user()
        if not user or user['role'] not in ('admin', 'chairman'):
            self._send_json({'error': 'forbidden'}, status=403)
            return
        rows = cur.execute('SELECT id, full_name, username, email, role, approved FROM users').fetchall()
        self._send_json([dict(r) for r in rows])

    def handle_role_update(self, user_id, data):
        user = self.auth_user()
        if not user or user['role'] not in ('admin', 'chairman'):
            self._send_json({'error': 'forbidden'}, status=403)
            return
        cur.execute('UPDATE users SET role = COALESCE(?, role), approved = COALESCE(?, approved) WHERE id = ?',
                    (data.get('role'), data.get('approved'), user_id))
        conn.commit()
        self._send_json({'status': 'updated'})


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 3001), Handler)
    print('Server running on port 3001')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
