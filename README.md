# Molpalata Telegram Mini App

This repository contains a simple implementation of a Telegram Mini App for the youth chamber.

* `backend_py/` – Python backend using only the standard library and SQLite
* `frontend/` – React frontend served as static HTML

## Running the backend

```bash
cd backend_py
python3 app.py
```

The backend also serves the frontend. After starting it, open
`http://localhost:3001/` in your browser or Telegram WebView to see the mini app.

## Running tests

```bash
cd backend_py
python3 -m unittest discover -s tests -v
```
