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
