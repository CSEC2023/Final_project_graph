# Declare phony targets to avoid conflicts with file names
.PHONY: help run docker-build docker-run clean venv install lint format tree test

# Default Docker image tag
TAG ?= graph-api:dev

help:
	@echo "Available commands:"
	@echo "  make venv           Create a local virtual environment (.venv)"
	@echo "  make install        Install dependencies into .venv"
	@echo "  make run            Run FastAPI using Uvicorn on port 8000"
	@echo "  make docker-build   Build Docker image (TAG=$(TAG))"
	@echo "  make docker-run     Run the full Docker Compose stack"
	@echo "  make lint           Run pylint on the application"
	@echo "  make format         Format code using Black"
	@echo "  make clean          Remove Python caches and temporary files"
	@echo "  make tree           Display project structure (depth 3)"
	@echo "  make test           Run pytest with coverage reporting"

# Create virtual environment only if it doesn't exist
venv:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		. .venv/bin/activate && pip install --upgrade pip; \
		echo "Created .venv"; \
	else \
		echo ".venv already exists"; \
	fi
	@echo "To activate manually: source .venv/bin/activate"

# Install all dependencies inside .venv
install: venv
	@. .venv/bin/activate && pip install -r requirements.txt

# Run the FastAPI application locally
run:
	@. .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Build Docker image
docker-build:
	docker build -t $(TAG) .

# Run entire stack (API + Neo4j + Nginx)
docker-run:
	docker-compose up --build

# Lint code with pylint (runs inside the API container)
lint:
	docker-compose exec api pylint app

# Format code using Black (if installed)
format:
	@if command -v black >/dev/null 2>&1; then \
		black app -l 120; \
	else \
		echo "black not installed (add it to requirements.txt)"; \
	fi

# Remove Python cache folders and compiled files
clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} \; || true
	find . -type f -name "*.pyc" -delete || true

# Display project tree (fallback to find if tree is missing)
tree:
	@if command -v tree >/dev/null 2>&1; then \
		tree -L 3 -I "node_modules|dist|.git|.venv|__pycache__"; \
	else \
		find . -maxdepth 3 -type d -not -path '*/\.*' | sort; \
	fi

# Run full test suite with coverage (inside the API container)
test:
	docker-compose up -d --build
	docker-compose exec api pytest --cov=app --cov-report=term

