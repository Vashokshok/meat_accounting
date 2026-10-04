# Выкладка на Linux-сервер

Production-запуск: FastAPI обслуживает API и готовые страницы из `frontend/`.
Next.js-прототип из `frontend/app/` на сервере не запускается.

## Требования

- Linux-сервер с публичным DNS-именем, указывающим на него.
- Docker Engine с плагином Docker Compose.
- Nginx и Certbot с плагином для Nginx.
- Открытые входящие порты 80 и 443.

## 1. Подготовить файлы и секреты

Получите код на сервер (клонируйте опубликованный Git-репозиторий или скопируйте
рабочую копию), перейдите в корень проекта и создайте `.env`:

```bash
cd /opt/meat_accounting
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
openssl rand -hex 32
```

Вставьте два разных результата команд в `.env`: первый как
`POSTGRES_PASSWORD`, второй как `SECRET_KEY`. Заполните доменное имя в
Nginx-конфигурации ниже. Не публикуйте и не коммитьте `.env`.

`SECRET_KEY` обязателен, должен содержать не менее 32 символов и не может быть
примером или стандартным значением. API откажется запускаться без него.
`DATABASE_URL` формируется Compose из настроек PostgreSQL в `.env`; миграции
автоматически используют тот же адрес с синхронным драйвером.

## 2. Запустить приложение

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 app
```

Контейнер `app` применяет миграции перед запуском Uvicorn без `--reload`.
PostgreSQL не публикует порт наружу, сохраняет данные в Docker volume и
стартует раньше API. API опубликован только на `127.0.0.1:8000` для Nginx.
Проверьте readiness:

```bash
curl --fail http://127.0.0.1:8000/api/v1/health
```

Создайте учётные записи сотрудников интерактивно. Повторный запуск не меняет
пароли существующих пользователей:

```bash
docker compose exec app python scripts/seed.py
```

Введите логин, пароль длиной 12–100 символов и подтверждение для каждого
сотрудника; пустой логин завершает ввод. Пароли не выводятся на экран.

## 3. Настроить HTTPS через Nginx

Убедитесь, что DNS-запись домена указывает на сервер. Установите конфигурацию:

```bash
sudo cp deploy/nginx/meat-accounting.conf /etc/nginx/sites-available/meat-accounting
```

В `/etc/nginx/sites-available/meat-accounting` замените `meat.example.com` на
ваш домен, включите сайт и выпустите сертификат:

```bash
sudo ln -s /etc/nginx/sites-available/meat-accounting /etc/nginx/sites-enabled/meat-accounting
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx --redirect -d ваш-домен
```

Проверьте `https://ваш-домен/` и вход сотрудника. Certbot добавит TLS-настройки
и перенаправление HTTP на HTTPS. API не должен быть доступен извне напрямую:
оставьте Compose-привязку к loopback и не открывайте порт 8000 в firewall.

## 4. Настроить и проверить резервное копирование

Скрипт использует ID контейнера БД, который возвращает Compose. Настройте каталог,
доступный пользователю cron и Docker:

```bash
sudo mkdir -p /var/backups/meat
sudo chmod 750 /var/backups/meat
chmod +x scripts/backup.sh
CONTAINER="$(docker compose ps -q db)" BACKUP_DIR=/var/backups/meat scripts/backup.sh
```

Убедитесь, что появился `.dump` и в логе есть `OK:`. Добавьте расписание
пользователю, который имеет доступ к Docker и каталогу резервных копий:

```cron
0 2 * * 1 cd /opt/meat_accounting && CONTAINER="$(docker compose ps -q db)" BACKUP_DIR=/var/backups/meat /opt/meat_accounting/scripts/backup.sh >> /var/backups/meat/cron.log 2>&1
```

В примере используются `DB_USER=meat` и `DB_NAME=meat`; если значения в `.env`
изменены, передайте соответствующие переменные скрипту. Скрипт хранит дампы 60
дней. Настройте копирование бэкапов на другой сервер
или объектное хранилище: резервная копия на том же диске не защищает от его
отказа.

Проверьте восстановление на отдельную базу (в примере используются настройки
по умолчанию `meat`):

```bash
DUMP=$(ls -t /var/backups/meat/meat_*.dump | head -1)
DB_CONTAINER=$(docker compose ps -q db)
docker exec -i "$DB_CONTAINER" createdb -U meat meat_restore_test
docker exec -i "$DB_CONTAINER" pg_restore -U meat -d meat_restore_test < "$DUMP"
docker exec -i "$DB_CONTAINER" dropdb -U meat meat_restore_test
```

## Проверка после перезапуска

```bash
docker compose restart
docker compose ps
curl --fail https://ваш-домен/api/v1/health
```

Убедитесь, что сервисы healthy, вход работает, данные сохранились после
перезапуска, HTTPS включён и тестовое восстановление прошло без ошибок.
