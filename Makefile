.PHONY: install run-flask run-django run-fastapi test test-flask test-django test-fastapi clean

ROOT := $(shell pwd)
VENV := $(ROOT)/venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV) 2>/dev/null || true
	$(PIP) install -r requirements.txt

# Run Flask app on port 8000
run-flask:
	cd $(ROOT) && $(PY) flask_app/app.py

# Run Django app on port 8000
run-django:
	cd $(ROOT)/django_app && $(PY) manage.py migrate && $(PY) manage.py runserver 0.0.0.0:8003

# Run FastAPI app on port 8000
run-fastapi:
	cd $(ROOT) && $(VENV)/bin/uvicorn fastapi_app.app:app --host 0.0.0.0 --port 8004

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
