# ==============================================================================
# DroidBridge Makefile
# Targets for running, testing, building Debian packages, and development.
# ==============================================================================

.PHONY: all run test build-deb clean install diagnostics help

PYTHON ?= python3
SHELL  := /bin/bash

all: build-deb

help:
	@echo "DroidBridge Development & Build Targets:"
	@echo "  make run          - Launch DroidBridge GUI in development mode"
	@echo "  make test         - Run comprehensive unit and integration tests"
	@echo "  make build-deb    - Build production Debian (.deb) package in dist/"
	@echo "  make diagnostics  - Run system dependency diagnostics in terminal"
	@echo "  make clean        - Remove build artifacts, staging directories, and pycache"

run:
	PYTHONPATH=src $(PYTHON) -m droidbridge.main

diagnostics:
	PYTHONPATH=src $(PYTHON) -m droidbridge.main --diagnostics

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

build-deb:
	chmod +x packaging/build_deb.sh
	./packaging/build_deb.sh

clean:
	rm -rf dist-deb/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
