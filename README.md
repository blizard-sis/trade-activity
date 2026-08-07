# Trade Activity

Локальная история сделок T‑Bank с группировкой позиций и помесячным отчётом.

## Структура

```text
backend/          Flask API, SQLite, T‑Bank и расчёты
frontend/src/     React-интерфейс
app.py            запуск приложения
config.json       локальные настройки и токен
```

## Первый запуск

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
Set-Location frontend
npm install
npm run build
Set-Location ..
```

Добавьте read-only токен T‑Invest API в `config.json`:

```json
{
  "tbank_token": "ваш токен",
  "port": 8000
}
```

Запуск:

```powershell
venv\Scripts\python.exe app.py
```

Откройте <http://127.0.0.1:8000>.

## Разработка фронтенда

Flask и Vite запускаются в двух терминалах:

```powershell
venv\Scripts\python.exe app.py
```

```powershell
Set-Location frontend
npm run dev
```

Интерфейс разработки: <http://127.0.0.1:5173>. Vite перенаправляет API-запросы во Flask.

После изменений соберите production-версию командой `npm run build`.
