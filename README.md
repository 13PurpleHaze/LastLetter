# LastLetter

## About The Project

LastLetter — это REST API, на базе FastAPI.
Проект предоставляет механизм создания и управления капсулами,
которые становятся доступными указанным пользователям при наступлении
определённых условий.

**Функционал:**
* Регистрация и аутентификация пользователей.
* Сброс пароля.
* Управление профилем пользователя.
* Подтверждение email при регистрации
* Email-уведомления о регистрации и сбросе пароля.
* Система ролей пользователей:
  * Родитель — создатель и владелец капсул.
  * Ребёнок — получатель доступа к капсулам при выполнении заданных условий.
  * Верификатор — пользователь, подтверждающий наступление события.
* Управление капсулами (создание, наполнение, просмотр, обновление, привязка пользователей)
* Генерация ссылок для загрузки фото и видео в капсулы и просмотра;
* Система инвайтов и связей между пользователями (родитель ↔ ребёнок, родитель ↔ верификатор)

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

### 1. Клонируй репозиторий

```bash
git clone https://github.com/your-username/capsule-time.git
cd capsule-time
```

### 2. Сгенерируйте ключи
```bash
mkdir -p certs secrets
openssl genrsa -out secrets/private.pem 2048
openssl rsa -in secrets/private.pem -outform PEM -pubout -out certs/public.pem
```
Сгенерируйте metrics_token, admin_token, rpc_secret для garage и запишите их в garage.toml и monitoring/prometheus.yml
```bash
openssl rand -hex 32
```

### 3. Запустите проект
Часть сервисов не будет работать, этот шаг нужен чтобы настроить garage
```bash
make deploy
```

### 4. Настройте Garage
Создайте бакет для медиа и трейсов(разные), далее создайте ключи и назначте их
```bash
docker compose exec garage /garage bucket create [имя бакета]
docker compose exec garage /garage key create [имя ключа]
docker compose exec garage /garage bucket allow --read --write --key [имя ключа] [имя бакета]
```
Ключи запишите в .env файл проекта


### 4. Настройте переменные окружения
Имена бакетов, регионы, ключи
```bash
cp .env.example .env
```

### 5. Пересоберите проект
```bash
make stop
make deploy
```

### 6. Запустите воркер dramatiq в контейнере с приложением
```bash
dramatiq modules.email.task
```
