# Как посмотреть старые бэкапы

Подробное руководство: от списка файлов до полного доступа к данным.
Всё показано для Windows (рабочая машина) и Linux (сервер).

## Где лежат бэкапы

| Машина | Путь | Формат имени файла |
|---|---|---|
| Windows | `C:\backups\meat` | `meat_ГГГГ-ММ-ДД_ЧЧММ.dump` |
| Linux | `/var/backups/meat` | `meat_ГГГГ-ММ-ДД_ЧЧММ.dump` |

Пример: `meat_2026-09-29_0101.dump` — бэкап, снятый 29 сентября 2026 в 01:01.
Файл зашифрован НЕ по-настоящему — он бинарный (формат custom), но содержимое
читается инструментами, описанными ниже.

## Шаг 0. Убедиться, что бэкапы вообще снимаются

```powershell
# Windows: лог (последняя строка "OK:" = успех)
Get-Content C:\backups\meat\backup.log -Tail 20

# Windows: статус задачи Планировщика
Get-ScheduledTaskInfo -TaskName MeatAccounting_WeeklyBackup
# LastTaskResult = 0 и свежий LastRunTime — бэкап прошёл успешно
```

```bash
# Linux
tail -20 /var/backups/meat/backup.log
crontab -l
```

Лог показывает, что именно произошло в 02:00 в понедельник: создан дамп,
удалён старый, сколько копий осталось.

## Способ 1. Список бэкапов

```powershell
# Windows: все дампы, новые сверху
Get-ChildItem C:\backups\meat\*.dump | Sort-Object LastWriteTime -Descending |
    Select-Object Name, Length, LastWriteTime
```

```bash
ls -lh /var/backups/meat/meat_*.dump
```

| Колонка | Что значит |
|---|---|
| `Length` | размер файла (меньше гигабайта — норм для этой системы) |
| `LastWriteTime` | когда снят бэкап («возраст» копии) |

## Способ 2. Структура дампа (что внутри)

Показывает каталог объектов: таблицы, секвенции, расширения. Ничего не меняет.

```powershell
# Windows
& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -l "C:\backups\meat\meat_2026-09-29_0101.dump"
```

```bash
# Linux (нужен установленный клиент PostgreSQL)
pg_restore -l /var/backups/meat/meat_2026-09-29_0101.dump
```

В выводе будут строки вида:

```
;     Archive created at 2026-09-28 21:55:57
;     dbname: meat          <- из какой базы снят
;     Format: CUSTOM
;     Dump Version: 1.16-0
;     Dumped from database version: 18.6
223; 1259 16406 TABLE public franchises ...
225; 1259 16421 TABLE public operations ...
```

Если `TABLE public ...` на месте — дамп целый. Пустой вывод с `pg_restore -l`
означает проблемы (см. `troubleshooting.md`).

## Способ 3. Данные прямо в консоль (без создания базы)

Достать содержимое таблиц как SQL-копии, ничего не создавая:

```powershell
# Windows: все данные всех таблиц
& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -a -f - "C:\backups\meat\meat_2026-09-29_0101.dump"

# Windows: только одна таблица (пример — operations)
& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -a -t operations -f - "C:\backups\meat\meat_2026-09-29_0101.dump"
```

```bash
# Linux
pg_restore -a -f - /var/backups/meat/meat_2026-09-29_0101.dump
pg_restore -a -t operations -f - /var/backups/meat/meat_2026-09-29_0101.dump
```

Флаги: `-a` = только данные, `-t <имя>` = одна таблица, `-f -` = выводить
в консоль (вместо файла). Данные появятся в виде:

```
COPY public.operations (id, type, meat_type, quantity, status, operation_date) FROM stdin;
1	INCOMING	FILLET	50.000	ACTIVE	2026-09-28
2	INCOMING	SKIN	30.000	ACTIVE	2026-09-28
\.
```

## Способ 4. Полный доступ: восстановить во временную базу

Единственный способ делать произвольные запросы (`SELECT`, `WHERE`, JOIN).

### Windows

```powershell
$dump = "C:\backups\meat\meat_2026-09-29_0101.dump"

# 1. Создаём пустую временную базу
docker exec -it meat_db psql -U meat -d meat -c "CREATE DATABASE meat_view;"

# 2. Льём дамп в неё
docker exec -i meat_db pg_restore -U meat -d meat_view < $dump

# 3. Смотрим данные
docker exec -it meat_db psql -U meat -d meat_view -c "select id, type, meat_type, quantity, status, operation_date from operations order by id desc limit 10;"

# 4. Убираем временную базу
docker exec -it meat_db psql -U meat -d meat -c "DROP DATABASE meat_view;"
```

### Linux

```bash
DUMP=/var/backups/meat/meat_2026-09-29_0101.dump

docker compose exec -T db createdb -U meat meat_view
docker compose exec -T db pg_restore -U meat -d meat_view < "$DUMP"
docker compose exec -T db psql -U meat -d meat_view -c "select * from users;"
docker compose exec -T db dropdb -U meat meat_view
```

Внутри `psql` (пароль `meat`):

```bash
docker compose exec db psql -U meat -d meat_view
meat_view=# \dt            -- список таблиц
meat_view=# select * from operation_changes;   -- история правок в JSONB
```

Полезные запросы для проверки:

```sql
select type, meat_type, sum(quantity) from operations
where status = 'ACTIVE' group by type, meat_type order by type;

select count(*) from operation_changes;  -- насколько велась история правок
```

## Автовыбор последнего бэкапа

Чтобы не вбивать имя файла вручную:

```powershell
# Windows
$dump = Get-ChildItem C:\backups\meat\*.dump |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
```

```bash
# Linux
DUMP=$(ls -t /var/backups/meat/meat_*.dump | head -1)
```

## Частые вопросы

**Почему файл не открывается в Блокноте?** Формат custom — бинарный архив
(заголовок `PGDMP` + каталог объектов + gzip-сжатые данные). Это не защита,
просто формат хранения без «лишнего» текста.

**Можно ли посмотреть данные без восстановления?** Да, способ 3
(`pg_restore -a -f -`) показывает содержимое как COPY-блоки.

**Редактировать дамп напрямую нельзя?** Нет. Любое изменение = риск повреждения.
Смотрение — только через `pg_restore`.

**Что там внутри с точки зрения данных?** Пользователи (включая bcrypt-хеши
паролей), операции учёта (тип, мясо, кг, дата, комментарии) и аудит правок
(`operation_changes` с «было → стало»). Доступ к файлу = доступ ко всей базе.