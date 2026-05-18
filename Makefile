# Smart Money Tracker — dev commands
.PHONY: setup migrate seed backend frontend test-security test-unit audit

setup:
	cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
	cd frontend && npm install

migrate:
	cd backend && .venv/Scripts/alembic upgrade head

seed:
	cd backend && .venv/Scripts/python scripts/seed.py

backend:
	cd backend && .venv/Scripts/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev

test-unit:
	cd backend && .venv/Scripts/pytest tests/unit/ -v

test-security:
	cd backend && .venv/Scripts/pytest tests/security/ -v

audit:
	cd backend && .venv/Scripts/bandit -r app -ll
	cd backend && .venv/Scripts/pip-audit -r requirements.txt
	cd frontend && npm audit --audit-level=high

dev: migrate seed
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "Run 'make backend' and 'make frontend' in separate terminals"
