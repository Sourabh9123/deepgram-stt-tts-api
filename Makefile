PYTHON ?= python
FRONTEND_DIR := frontend

.PHONY: install-backend install-frontend install local api frontend test format lint frontend-build build docker-up

install-backend:
	$(PYTHON) -m pip install -r requirements.txt

install-frontend:
	npm --prefix $(FRONTEND_DIR) install

install: install-backend install-frontend

local:
	$(MAKE) -j2 api frontend

api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	npm --prefix $(FRONTEND_DIR) run dev

test:
	pytest

format:
	black app tests examples
	isort app tests examples

lint:
	black --check app tests examples
	isort --check-only app tests examples

frontend-build:
	npm --prefix $(FRONTEND_DIR) run build

build: frontend-build

docker-up:
	docker compose up --build -d
