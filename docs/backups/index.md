# Документация по бэкапам

Все инструкции, связанные с резервным копированием БД `meat`, собраны здесь.

## Как устроена система

| Компонент | Значение |
|---|---|
| Скрипт (Windows) | `scripts/backup.ps1` |
| Скрипт (Linux) | `scripts/backup.sh` |
| Контейнер БД | PostgreSQL 18 через Compose (внутренняя сеть, постоянный volume) |
| Формат дампа | PostgreSQL custom (`pg_dump -Fc -Z9`, сжатие gzip) |
| Каталог бэкапов | Windows: `C:\backups\meat`, Linux: `/var/backups/meat` |
| Ротация | хранится 60 дней (2 месяца), старше — удаляются автоматически |
| Лог | `backup.log` в каталоге бэкапов |
| Расписание | каждый понедельник в 02:00 |
| Задача (Windows) | `MeatAccounting_WeeklyBackup` в Планировщике |
| Cron (Linux) | настраивается при выкладке, см. `deploy.md` |

Цикл каждого бэкапа: `pg_dump` (custom, сжатие 9) внутри контейнера →
`docker cp` на хост → проверка целостности (размер, заголовок `PGDMP`,
`pg_restore -l` внутри контейнера БД, чтобы избежать несовпадения версий
PostgreSQL на хосте и в контейнере) → ротация (удаление старше 60 дней) →
запись в `backup.log`.

## Документы

| Файл | О чём |
|---|---|
| `view-backups.md` | Как посмотреть старые бэкапы: список, структура, данные, временная база (подробно) |
| `restore.md` | Как восстановить базу из бэкапа: полное, выборочное, в другую базу |
| `deploy.md` | Production-выкладка через Compose, Nginx/HTTPS, cron и проверка восстановления |
| `troubleshooting.md` | Типовые проблемы, мониторинг, правила для прода |

## Быстрая шпаргалка

```powershell
# Windows: последние бэкапы
Get-ChildItem C:\backups\meat\*.dump | Sort-Object LastWriteTime -Descending

# Windows: лог
Get-Content C:\backups\meat\backup.log -Tail 20

# Windows: статус задачи
Get-ScheduledTaskInfo -TaskName MeatAccounting_WeeklyBackup
```

```bash
# Linux: бэкапы и лог
ls -lh /var/backups/meat/meat_*.dump
tail -20 /var/backups/meat/backup.log
crontab -l
```