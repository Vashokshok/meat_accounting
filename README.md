# Meat accounting

Внутренний учёт мяса для одной точки: 3 сотрудника, 2 вида мяса (филе / с кожей),
5 типов операций, остатки из операций, аудит правок, отчёты и экспорт в Excel.

Стек: FastAPI + PostgreSQL + SQLAlchemy 2.0 (async) + Alembic + JWT.

## Правила учёта

- Остаток не вводится вручную: `INCOMING` — плюс, `SPIT / WRITE_OFF / CONVECTION /
  FRANCHISE` — минус. Филе и кожа считаются отдельно.
- Расход ниже нуля запрещён — проверка в транзакции (`pg_advisory_xact_lock`
  по виду мяса). То же при правке и отмене прихода.
- Удаления нет: отмена ставит `CANCELLED`. Отменённое не влияет на остаток.
- Каждая правка/отмена пишет аудит: было → стало → кто → когда.
- Даты и отчёты — по `operation_date` (можно задним числом), часовой пояс
  `Europe/Moscow`.

## Ручки

Все (кроме `health` и `login`) требуют `Authorization: Bearer <token>`.

| Метод | URL | Что делает |
|---|---|---|
| GET | `/api/v1/health` | Проверка API и связи с БД |
| POST | `/api/v1/auth/login` | Вход `{username, password}` → `access_token` (24ч) |
| GET | `/api/v1/auth/me` | Текущий пользователь |
| POST | `/api/v1/operations` | Новая операция (201) |
| GET | `/api/v1/operations` | История: `date_from/date_to/type/meat_type/user_id/franchise_id/status`, `limit/offset` |
| GET | `/api/v1/operations/{id}` | Одна операция |
| PATCH | `/api/v1/operations/{id}` | Правка (всё кроме `status`) + аудит |
| POST | `/api/v1/operations/{id}/cancel` | Отмена (`CANCELLED`) + аудит |
| GET | `/api/v1/operations/{id}/changes` | История изменений операции |
| GET | `/api/v1/stock` | Текущие остатки `{fillet, skin}` |
| GET | `/api/v1/franchises` | Справочник (`?active_only=true`) |
| POST | `/api/v1/franchises` | Новая франшиза |
| PATCH | `/api/v1/franchises/{id}` | Переименование / отключение |
| GET | `/api/v1/reports?period=today\|week\|month\|custom` | Отчёт по видам мяса: на начало, движение, на конец (`custom` + `date_from/date_to`) |
| GET | `/api/v1/exports/excel` | Excel: листы «Сводка», «Операции», «История изменений» |

Ошибки на русском: `409 INSUFFICIENT_STOCK` («Недостаточно мяса…»),
`409 ALREADY_CANCELLED`, `401`, `404`. Доки: `/docs`.

## Запуск

```bash
# 1. База
docker run -d --name meat_db --restart unless-stopped \
  -e POSTGRES_USER=meat -e POSTGRES_PASSWORD=meat -e POSTGRES_DB=meat \
  -p 127.0.0.1:5434:5432 postgres:18-alpine

# 2. Зависимости
python3 -m venv ../venv && ../venv/bin/pip install -r requirements.txt

# 3. Миграции и seed (admin/user1/user2, пароль meat123)
../venv/bin/alembic upgrade head
../venv/bin/python scripts/seed.py

# 4. API
../venv/bin/uvicorn app.main:app --reload --port 8000
```

Тесты (нужна БД `meat_test` на том же Postgres):

```bash
docker exec meat_db psql -U meat -c "CREATE DATABASE meat_test"
../venv/bin/python -m pytest tests/ -q
../venv/bin/ruff check app scripts tests
```

Переменные (`.env`): `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_HOURS=24`,
`TIMEZONE=Europe/Moscow`.
