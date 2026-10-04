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
| PATCH | `/api/v1/auth/profile` | Изменение имени, логина и/или пароля (требует текущий пароль) |
| POST | `/api/v1/operations` | Новая операция (201) |
| GET | `/api/v1/operations` | История: `date_from/date_to/type/meat_type/user_id/franchise_id/status`, `limit/offset` |
| DELETE | `/api/v1/operations/history?period=day&operation_date=YYYY-MM-DD` | Безвозвратно удалить операции за день (`period=last_month` или `period=all`); связанный аудит удаляется |
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

### Сервер

Production-развёртывание через Docker Compose (PostgreSQL + API) и Nginx описано
в [`docs/backups/deploy.md`](docs/backups/deploy.md). Для API и пользовательского
интерфейса используется FastAPI: он обслуживает готовые HTML-страницы из
`frontend/`. Каталог `frontend/app/` — отдельный незавершённый прототип Next.js,
в production-конфигурацию он не входит.

### Локальная разработка

Требуется Python 3.12 или новее.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Создайте `.env` с `DATABASE_URL` и случайным `SECRET_KEY` (не короче 32
символов). Для локальной БД используйте PostgreSQL. Затем выполните `alembic
upgrade head`, `python scripts/seed.py` и запустите
`uvicorn app.main:app --reload --port 8000`. Seed запросит логины и пароли
сотрудников интерактивно; стандартных пользователей и паролей нет.

## Бэкапы

Бэкапы, расписание и восстановление описаны в `docs/backups/`. Не храните
единственную копию на том же сервере, что и база.

Тесты (нужна отдельная БД `meat_test` на PostgreSQL):

```bash
createdb meat_test
pip install -r requirements-dev.txt
pytest tests/ -q
ruff check app scripts tests
```

Обязательные переменные `.env`: `DATABASE_URL` и криптографически случайный
`SECRET_KEY` длиной от 32 символов. Дополнительно можно задать
`ACCESS_TOKEN_EXPIRE_HOURS` и `TIMEZONE`.
