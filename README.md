# Trade Activity

Локальная история сделок T‑Bank с группировкой позиций и помесячным отчётом.

## Структура

```text
backend/          Flask API, SQLite, T‑Bank и расчёты
frontend/src/     React-интерфейс
app.py            запуск приложения
pyproject.toml    метаданные проекта и зависимости Python
config.json       локальные настройки и токен
```

## Первый запуск

Нужны Python 3.10+ и Node.js 20.19+ в ветке 20 либо 22.12+.
Все команды выполняются из корня проекта, если не указано иначе.
Python-зависимости описаны в `pyproject.toml`. Установка через `pip install -e .`
связывает окружение с исходниками проекта; приложение запускается из этого checkout.

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
cd frontend
npm ci
npm run build
cd ..
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
Set-Location frontend
npm ci
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

```bash
# macOS / Linux
.venv/bin/python app.py
```

```powershell
# Windows PowerShell
.venv\Scripts\python.exe app.py
```

Откройте <http://127.0.0.1:8000>.

## Разработка фронтенда

Flask и Vite запускаются в двух терминалах:

```bash
# macOS / Linux (Windows: .venv\Scripts\python.exe app.py)
.venv/bin/python app.py
```

```bash
cd frontend
npm run dev
```

Интерфейс разработки: <http://127.0.0.1:5173>. Vite перенаправляет API-запросы во Flask.

После изменений соберите production-версию командой `npm run build`.
