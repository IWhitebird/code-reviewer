.PHONY: install run fastapi celery

VENV_NAME := .venv
PYTHON := python3
PIP := $(VENV_NAME)/bin/pip
VENV_ACTIVATE := . $(VENV_NAME)/bin/activate

install:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_NAME)
	@echo "Activating virtual environment and installing dependencies..."
	$(VENV_ACTIVATE) && \
	$(PIP) install --upgrade pip && \
	$(PIP) install -r requirements.txt
	@echo "Installation complete! ✨ Run 'make run' to start the services."

run: fastapi celery

fastapi:
	$(VENV_ACTIVATE) && python3 -m fastapi dev

celery:
	$(VENV_ACTIVATE) && celery -A app.worker.celery_app.celery_app worker --loglevel=debug -E