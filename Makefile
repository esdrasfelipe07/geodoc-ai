.PHONY: help build up down dev logs test clean

help:
	@echo "Comandos disponíveis para GeoDoc AI:"
	@echo "  make build    - Constrói as imagens Docker de produção"
	@echo "  make up       - Inicia os containers de produção em background"
	@echo "  make dev      - Inicia ambiente de desenvolvimento com hot-reload"
	@echo "  make down     - Para e remove os containers ativos"
	@echo "  make logs     - Visualiza os logs dos containers em tempo real"
	@echo "  make test     - Executa a suíte de testes automatizados com pytest"
	@echo "  make clean    - Remove dados temporários e volumes órfãos do Docker"

build:
	docker compose build

up:
	docker compose up -d --build
	@echo "Aplicação iniciada:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend API / Docs: http://localhost:8000/docs"

dev:
	docker compose -f docker-compose.dev.yml up

down:
	docker compose down --remove-orphans

logs:
	docker compose logs -f

test:
	docker compose run --rm backend pytest -v

clean:
	docker compose down -v --remove-orphans
	docker system prune -f
