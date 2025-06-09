# Сайт Молодёжной палаты района Некрасовка

Простой пример сайта для палаты. Реализована регистрация, вход и просмотр мероприятий.

* `backend_py/` – Python backend using only the standard library and SQLite
* `backend_node/` – optional Node.js backend
* `frontend/` – React frontend served as static HTML

## Running the backend

```bash
cd backend_py
python3 app.py
```

После запуска сервер будет доступен на `http://localhost:3001/` и отдаст страницу `frontend/index.html`.

На сайте можно зарегистрироваться или войти в систему. Регистрация требует ФИО, дату рождения, телефон, Telegram username, e‑mail и пароль.

Пример регистрации через curl:

```bash
curl -X POST http://localhost:3001/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"Test","birth_date":"2000-01-01","phone":"123","email":"test@example.com","password":"pass"}'
```

Then log in using the same email and password. After successful login you will see the list of events.

При создании мероприятия баллы назначаются автоматически в зависимости от категории (например, "meeting" = 10, "social_action" = 6).

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
