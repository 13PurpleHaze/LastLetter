DOCKER_COMPOSE_PATH = docker/docker-compose.yml
ENV_FILE = .env

deploy:
	docker compose -f ${DOCKER_COMPOSE_PATH} --env-file $(ENV_FILE) up -d --build

stop:
	docker compose -f ${DOCKER_COMPOSE_PATH} down

logs:
	docker compose -f $(DOCKER_COMPOSE_PATH) logs -f

restart:
	docker compose -f ${DOCKER_COMPOSE_PATH} --env-file $(ENV_FILE) up -d --build --force-recreate
