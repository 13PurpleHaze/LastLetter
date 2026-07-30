# LastLetter

## About The Project

LastLetter — это REST API на базе FastAPI для создания цифровых капсул времени.

Проект предоставляет механизм создания и управления капсулами,
которые становятся доступными указанным пользователям после наступления
заданного события, подтверждённого доверенным верификатором.


## **Функционал:**
### Authentication & Users
- Регистрация пользователей
- JWT-аутентификация
- Подтверждение email
- Сброс пароля
- Управление профилем пользователя
### User Roles
- Parent — создатель и владелец капсул
- Child — пользователь, получающий доступ к капсулам при выполнении условий
- Verifier — пользователь, подтверждающий наступление события
### Relationships
- Связи между пользователями: Parent ↔ Child Parent ↔ Verifier
- Система инвайтов для создания связей
### Capsules
- Создание и управление капсулами
- Добавление пользователей к капсулам
- Наполнение капсул сообщениями и медиафайлами
- Генерация ссылок для: загрузки фото и видео; просмотра содержимого капсул
### Notifications
Email-уведомления:
- подтверждение регистрации;
- восстановление пароля;
- отправка ссылок доступа

Событие - это смерть автора капсулы

## Built With

Проект создан с использованием следующих технологий:

* ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
* ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
* ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
* ![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
* ![Dramatiq](https://img.shields.io/badge/Dramatiq-5E35B1?style=for-the-badge)
* ![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
* ![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)
![Grafana Tempo](https://img.shields.io/badge/Grafana_Tempo-F46800?style=for-the-badge&logo=grafana&logoColor=white)
![Grafana Loki](https://img.shields.io/badge/Grafana_Loki-F46800?style=for-the-badge&logo=grafana&logoColor=white)


## Get started

### 0. Установите необходимые зависимости
Перед запуском необходимо установить [Docker](https://docs.docker.com/)

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/13PurpleHaze/LastLetter.git
cd LastLetter
```

### 2. Сгенерируйте ключи
Ключи для аутентификации:
```bash
mkdir -p certs secrets
openssl genrsa -out secrets/private.pem 2048
openssl rsa -in secrets/private.pem -outform PEM -pubout -out certs/public.pem
```
Ключи для metrics_token, admin_token, rpc_secret для garage.
```bash
openssl rand -hex 32
```
запишите их в garage.toml и monitoring/prometheus.yml
```toml
## garage.toml
rpc_bind_addr = "[::]:3901"
rpc_public_addr = "127.0.0.1:3901"
rpc_secret = "..." <- сюда
...
api_bind_addr = "0.0.0.0:3903"
admin_token = "..." <- сюда
metrics_token = "..." <- сюда
```

```yml
## monitoring/prometheus.yml
...
  - job_name: 'garage'
    static_configs:
      - targets:
          - 'garage:3903'
    authorization:
      type: Bearer
      credentials: '...' <- сюда
```


### 3. Сконфигурируйтете garage
Нам нужно создать 2 бакета: первый для медиафайлов капсул, второй для трейсов. Для этого нужно пройти эти шаги

Запустите контейнер только с garage
```bash
docker compose -f=docker/docker-compose.yml --env-file=.env up garage 
```
Получите ID узла
```bash
docker compose -f=docker/docker-compose.yml --env-file=.env exec garage /garage status
...
==== HEALTHY NODES ====
ID                Hostname      Address         Tags  Zone  Capacity          DataAvail  Version
4619a172fdcf58a0  0080c32bcdbf  127.0.0.1:3901              NO ROLE ASSIGNED             v2.3.0
```
Допустим наш ID это 4619a172fdcf58a0.
Далее создайте layout и примените
```bash
docker compose -f=docker/docker-compose.yml --env-file=.env exec garage \
  /garage layout assign -z dc1 -c 1G 4619a172fdcf58a0
  
docker compose -f=docker/docker-compose.yml --env-file=.env exec garage \
  /garage layout apply --version 1
```
Сойздайте bucket. Его имя запишите в .env в `S3_BUCKET_NAME`
```bash
docker compose -f=docker/docker-compose.yml --env-file=.env exec garage \
  /garage bucket create ИМЯ_БАКЕТА
...
==== BUCKET INFORMATION ====
Bucket:          f3ee6831e885de553f78715c4dc239b251829c66e71c93244ca82c3be18d2f51
Created:         2026-07-30 05:11:42.127 +00:00

Size:            0 B (0 B)
Objects:         0

Website access:  false

Global alias:    lastletter

==== KEYS FOR THIS BUCKET ====
Permissions  Access key    Local aliases
```
Создайте ключи. Сохраните Key ID и Secret key в .env файл поля `S3_ACCESS_KEY` и `S3_SECRET_KEY` соответственно.
```bash
docker compose -f=docker/docker-compose.yml --env-file=.env exec garage \
  /garage key create ИМЯ_КЛЮЧА
...
==== ACCESS KEY INFORMATION ====
Key ID:              GKc3721315ddaaad62efa155da
Key name:            ...
Secret key:          7fc5da3dfa32ad5de68cd0e8d170aa6f74cc601f7589d94c3b51cb21ea607ce7
Created:             2026-07-30 05:14:23.831 +00:00
Validity:            valid
Expiration:          never

Can create buckets:  false

==== BUCKETS FOR THIS KEY ====
Permissions  ID  Global aliases  Local aliases
```
Назначте ключи на созданный bucket
```bash
docker compose -f=docker/docker-compose.yml --env-file=.env exec garage \
  /garage bucket allow --read --write --key ИМЯ_КЛЮЧА ИМЯ_БАКЕТА
```
Абсолютно аналогично сделайте и для бакета трейсов, только не создавайте новый layout, а только бакет и запишите результаты в `TRACE_S3_ACCESS_KEY`, `TRACE_S3_BUCKET_NAME`, `TRACE_S3_SECRET_KEY` 

Остановите контейнер с garage
```bash
docker compose -f=docker/docker-compose.yml --env-file=.env stop garage
```

### 4. Соберите проект
```bash
make deploy
```

### 5. Запустите воркер dramatiq в контейнере с приложением
```bash
dramatiq modules.email.tasks
```
