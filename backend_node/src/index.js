const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const path = require('path');
const app = express();
const db = new sqlite3.Database('./db.sqlite');
app.use(express.json());
app.use(express.static(path.join(__dirname, '..', '..', 'frontend')));
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', '..', 'frontend', 'index.html'));
});

const SECRET = 'secret-key';

// Create tables if not exist
const userTable = `CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT,
  birth_date TEXT,
  phone TEXT,
  username TEXT,
  email TEXT UNIQUE,
  password TEXT,
  role TEXT DEFAULT 'candidate',
  approved INTEGER DEFAULT 0
)`;
const eventTable = `CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  datetime TEXT,
  category TEXT,
  points INTEGER,
  description TEXT
)`;
const attendanceTable = `CREATE TABLE IF NOT EXISTS attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  event_id INTEGER,
  attended INTEGER,
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(event_id) REFERENCES events(id)
)`;

db.serialize(() => {
  db.run(userTable);
  db.run(eventTable);
  db.run(attendanceTable);
});

function authMiddleware(req, res, next) {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).json({ error: 'No token' });
  jwt.verify(token.split(' ')[1], SECRET, (err, decoded) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = decoded;
    next();
  });
}

app.post('/api/auth/register', (req, res) => {
  const { full_name, birth_date, phone, username, email, password } = req.body;
  const hash = bcrypt.hashSync(password, 10);
  const stmt = db.prepare('INSERT INTO users (full_name, birth_date, phone, username, email, password) VALUES (?, ?, ?, ?, ?, ?)');
  stmt.run(full_name, birth_date, phone, username, email, hash, function(err) {
    if (err) return res.status(400).json({ error: err.message });
    res.json({ id: this.lastID });
  });
});

app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;
  db.get('SELECT * FROM users WHERE email = ?', [email], (err, user) => {
    if (err || !user) return res.status(400).json({ error: 'User not found' });
    if (!bcrypt.compareSync(password, user.password)) return res.status(400).json({ error: 'Invalid password' });
    const token = jwt.sign({ id: user.id, role: user.role }, SECRET);
    res.json({ token });
  });
});

app.get('/api/events', authMiddleware, (req, res) => {
  db.all('SELECT * FROM events', (err, rows) => {
    if (err) return res.status(400).json({ error: err.message });
    res.json(rows);
  });
});

app.post('/api/events', authMiddleware, (req, res) => {
  if (req.user.role !== 'admin' && req.user.role !== 'chairman') return res.status(403).json({ error: 'Forbidden' });
  const { title, datetime, category, points, description } = req.body;
  const stmt = db.prepare('INSERT INTO events (title, datetime, category, points, description) VALUES (?, ?, ?, ?, ?)');
  stmt.run(title, datetime, category, points, description, function(err) {
    if (err) return res.status(400).json({ error: err.message });
    res.json({ id: this.lastID });
  });
});

app.post('/api/attendance', authMiddleware, (req, res) => {
  const { event_id, attended } = req.body;
  const stmt = db.prepare('INSERT OR REPLACE INTO attendance (user_id, event_id, attended) VALUES (?, ?, ?)');
  stmt.run(req.user.id, event_id, attended ? 1 : 0, function(err) {
    if (err) return res.status(400).json({ error: err.message });
    res.json({ id: this.lastID });
  });
});

app.get('/api/users', authMiddleware, (req, res) => {
  if (req.user.role !== 'admin' && req.user.role !== 'chairman') return res.status(403).json({ error: 'Forbidden' });
  db.all('SELECT id, full_name, username, email, role, approved FROM users', (err, rows) => {
    if (err) return res.status(400).json({ error: err.message });
    res.json(rows);
  });
});

app.post('/api/roles/:id', authMiddleware, (req, res) => {
  if (req.user.role !== 'admin' && req.user.role !== 'chairman') return res.status(403).json({ error: 'Forbidden' });
  const { role, approved } = req.body;
  const stmt = db.prepare('UPDATE users SET role = COALESCE(?, role), approved = COALESCE(?, approved) WHERE id = ?');
  stmt.run(role, approved, req.params.id, function(err) {
    if (err) return res.status(400).json({ error: err.message });
    res.json({ updated: this.changes });
  });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
