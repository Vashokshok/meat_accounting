# Восстановление из бэкапа

Полное и выборочное восстановление БД `meat` из дампа custom.

## Правила перед восстановлением

1. Восстанавливаем ТОЛЬКО в пустую базу или с `--clean --if-exists`.
   Поверх живых данных одного дампа — нельзя.
2. Если восстанавливаем на рабочую базу: сначала остановить приложение
   (`docker compose stop app` на Linux; остановить Uvicorn на Windows), чтобы
   во время восстановления никто не писал в БД.
3. Перед восстановлением крупных данных сделать свежий дамп текущего состояния.
4. Смотреть и восстанавливать — только через `pg_restore`, не трогая файл руками
   (он бинарный, правка ломает дамп).

## Полное восстановление

```bash
# Windows
docker exec -i meat_db pg_restore -U meat -d meat --clean --if-exists < C:\backups\meat\meat_2026-09-29_0101.dump

# Linux
docker compose exec -T db pg_restore -U meat -d meat --clean --if-exists < /var/backups/meat/meat_2026-09-29_0101.dump
```

`--clean` — удалить существующие объекты перед созданием;
`--if-exists` — не падать, если объект не найден.

## Восстановление в пустую базу (для проверки)

```bash
# Windows
docker exec -it meat_db psql -U meat -d meat -c "CREATE DATABASE meat_restore_test;"
docker exec -i meat_db pg_restore -U meat -d meat_restore_test < C:\backups\meat\meat_2026-09-29_0101.dump

# Linux
docker compose exec -T db createdb -U meat meat_restore_test
docker compose exec -T db pg_restore -U meat -d meat_restore_test < /var/backups/meat/meat_2026-09-29_0101.dump
```

## Выборочное восстановление (одна таблица)

```bash
# данные таблицы operations в существующую базу
docker compose exec -T db pg_restore -U meat -d meat_restore_test -t operations < /var/backups/meat/meat_2026-09-29_0101.dump

# структура конкретной таблицы (без данных)
docker compose exec -T db pg_restore -U meat -d meat_restore_test -t operations --schema-only < /var/backups/meat/meat_2026-09-29_0101.dump
```

## Восстановление в другую базу с переименованием

```bash
docker compose exec -T db createdb -U meat meat_new
docker compose exec -T db pg_restore -U meat -d meat_new --no-owner --no-privileges < /var/backups/meat/meat_2026-09-29_0101.dump
```

`--no-owner` — владельцы объектов из дампа не применяются (полезно при
переносе на другой сервер).

## Проверка после восстановления

```bash
# Сколько операций восстановилось
docker compose exec -T db psql -U meat -d meat -c "select count(*) from operations;"

# Видны ли остатки двух видов мяса
docker compose exec -T db psql -U meat -d meat -c "select meat_type, sum(quantity) from operations where status='ACTIVE' group by meat_type;"
```

## Автовыбор файла

```powershell
# Windows
$dump = Get-ChildItem C:\backups\meat\*.dump | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
```

```bash
# Linux
DUMP=$(ls -t /var/backups/meat/meat_*.dump | head -1)
```

## Полная последовательность для сценария «база умерла»

```powershell
# 1. Остановить приложение
# 2. Пересоздать пустую базу
docker exec -it meat_db psql -U meat -d meat -c "DROP DATABASE IF EXISTS meat;"
docker exec -it meat_db psql -U meat -d meat -c "CREATE DATABASE meat;"

# 3. Восстановить последний дамп
$dump = Get-ChildItem C:\backups\meat\*.dump | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
docker exec -i meat_db pg_restore -U meat -d meat < $dump

# 4. Проверить и запустить приложение
docker exec -it meat_db psql -U meat -d meat -c "select count(*) from operations;"
```