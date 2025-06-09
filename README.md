# Molpalata Web App

This repository contains a simple web application for the youth chamber.

* `backend_py/` – Python backend using only the standard library and SQLite
* `backend_node/` – optional Node.js backend
* `frontend/` – React frontend served as static HTML

## Running the backend

```bash
cd backend_py
python3 app.py
```

The backend also serves the frontend. After starting it, open
`http://localhost:3001/` in your browser to see the site.

The app now shows a simple login form. Create a user via the registration API, for example:

```bash
curl -X POST http://localhost:3001/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"Test","birth_date":"2000-01-01","phone":"123","email":"test@example.com","password":"pass"}'
```

Then log in using the same email and password. After successful login you will see the list of events.

### Node.js backend (optional)

Alternatively you can run the Node.js version of the backend:

```bash
cd backend_node
npm install   # only needed the first time
npm start
```

It serves the same frontend on `http://localhost:3001/`.

## Running tests

```bash
cd backend_py
python3 -m unittest discover -s tests -v
```
