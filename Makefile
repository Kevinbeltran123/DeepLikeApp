.PHONY: help setup setup-backend setup-frontend dev backend frontend build clean

PYTHON := python3.12

help:
	@echo "DeepLikeApp"
	@echo ""
	@echo "  make setup           Install backend and frontend dependencies"
	@echo "  make setup-backend   Create venv and install Python deps"
	@echo "  make setup-frontend  Install Node deps"
	@echo "  make backend         Run FastAPI on port 8000"
	@echo "  make frontend        Run Vite dev server on port 5173"
	@echo "  make dev             Reminder to run backend and frontend in two terminals"
	@echo "  make build           Build frontend for production"
	@echo "  make clean           Remove venv, node_modules and build outputs"

setup: setup-backend setup-frontend

setup-backend:
	cd backend && $(PYTHON) -m venv .venv
	cd backend && . .venv/bin/activate && pip install --upgrade pip
	cd backend && . .venv/bin/activate && pip install -r requirements.txt
	cd backend && cp -n .env.example .env || true

setup-frontend:
	cd frontend && npm install

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Run 'make backend' and 'make frontend' in two separate terminals."

build:
	cd frontend && npm run build

clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist
