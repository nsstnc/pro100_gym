COMPOSE_FILE = docker-compose.yml

.PHONY: build up down

build:
	docker-compose -f $(COMPOSE_FILE) build

up:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down

help:
	@echo Available commands:
	@echo   make build  - build containers
	@echo   make up     - up containers
	@echo   make down   - stop and delete containers