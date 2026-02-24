.PHONY: install run-flask run-django run-fastapi run-all stop-all test test-flask test-django test-fastapi clean

ROOT := $(shell pwd)
VENV := $(ROOT)/venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PIDS_FILE := $(ROOT)/.pids

install:
	python3 -m venv $(VENV) 2>/dev/null || true
	$(PIP) install -r requirements.txt

# Run Flask app on port 8002
run-flask:
	cd $(ROOT) && $(PY) flask_app/app.py

# Run Django app on port 8003
run-django:
	cd $(ROOT)/django_app && $(PY) manage.py migrate && $(PY) manage.py runserver 0.0.0.0:8003

# Run FastAPI app on port 8004
run-fastapi:
	cd $(ROOT) && $(VENV)/bin/uvicorn fastapi_app.app:app --host 0.0.0.0 --port 8004

# Run all 3 apps in background (Flask=8002, Django=8003, FastAPI=8004)
run-all:
	@rm -f $(PIDS_FILE)
	@echo "Starting Flask on port 8002..."
	@cd $(ROOT) && nohup $(PY) flask_app/app.py > /dev/null 2>&1 & echo $$! >> $(PIDS_FILE)
	@echo "Starting Django on port 8003..."
	@cd $(ROOT)/django_app && $(PY) manage.py migrate --no-input 2>/dev/null || true; \
		nohup $(PY) manage.py runserver 0.0.0.0:8003 > /dev/null 2>&1 & echo $$! >> $(PIDS_FILE)
	@echo "Starting FastAPI on port 8004..."
	@cd $(ROOT) && nohup $(VENV)/bin/uvicorn fastapi_app.app:app --host 0.0.0.0 --port 8004 > /dev/null 2>&1 & echo $$! >> $(PIDS_FILE)
	@echo "All servers started: Flask (8002), Django (8003), FastAPI (8004)"
	@echo "Run 'make stop-all' to stop them."

# Stop all running servers
stop-all:
	@if [ -f $(PIDS_FILE) ]; then \
		echo "Stopping servers..."; \
		while read pid; do kill $$pid 2>/dev/null || true; done < $(PIDS_FILE); \
		rm -f $(PIDS_FILE); \
		echo "All servers stopped."; \
	else \
		echo "No servers running (run 'make run-all' first)."; \
	fi

# Run all tests
test: test-flask test-django test-fastapi

test-flask:
	cd $(ROOT) && $(PY) -m pytest tests/test_flask_app.py -v

test-django:
	cd $(ROOT)/django_app && $(PY) manage.py test shortener --verbosity=2

test-fastapi:
	cd $(ROOT) && $(PY) -m pytest tests/test_fastapi_app.py -v

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -f flask_app/*.db django_app/db.sqlite3 fastapi_app/*.db tests/*.db *.db 2>/dev/null || true
