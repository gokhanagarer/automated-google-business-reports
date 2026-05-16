.PHONY: install demo test lint clean help

PY := python3
VENV := .venv
ACTIVATE := . $(VENV)/bin/activate

help:
	@echo "Targets:"
	@echo "  install   create venv and install runtime deps"
	@echo "  demo      run end-to-end on the bundled fixture (no API keys)"
	@echo "  test      run unit + integration tests"
	@echo "  lint      ruff check + format check"
	@echo "  clean     remove venv, caches, generated reports"

$(VENV):
	$(PY) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip --quiet

install: $(VENV)
	$(ACTIVATE) && pip install -r requirements.txt --quiet

install-dev: $(VENV)
	$(ACTIVATE) && pip install -r requirements-dev.txt --quiet

demo: install
	$(ACTIVATE) && $(PY) -m src.demo

test: install-dev
	$(ACTIVATE) && $(PY) -m pytest -q

lint: install-dev
	$(ACTIVATE) && pip install ruff --quiet && ruff check src tests

clean:
	rm -rf $(VENV) .pytest_cache reports
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
