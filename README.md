# Trade Activity

Локальная история сделок из T‑Invest API: синхронизация в SQLite и просмотр в веб-таблице.

## Запуск

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Запишите read-only токен T‑Invest API в `config.json`:

```json
{
  "tbank_token": "ваш токен",
  "port": 8000
}
```

Затем:

```powershell
python app.py
```

Откройте <http://127.0.0.1:8000> и нажмите «Синхронизировать».

Данные сохраняются в `trade_activity.sqlite3`. Повторная синхронизация обновляет сделки без дублей.
