.PHONY: install install-sys-deps run run-debug lint test clean

VENV    := .venv
PYTHON  := $(VENV)/bin/python
UV      := uv

PS5_IP ?= 192.168.1.3

SDL2_PREFIX := $(shell brew --prefix sdl2 2>/dev/null)

install-sys-deps:
	brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf

install: install-sys-deps
	$(UV) venv $(VENV)
	CFLAGS="-I$(SDL2_PREFIX)/include -I$(SDL2_PREFIX)/include/SDL2" \
	LDFLAGS="-L$(SDL2_PREFIX)/lib" \
	$(UV) pip install -e ".[dev]"

run:
	SIMRACING_DEVICE_IP=$(PS5_IP) $(PYTHON) -m simracing.main

run-debug:
	SIMRACING_DEVICE_IP=$(PS5_IP) $(PYTHON) -m simracing.main --debug

lint:
	$(VENV)/bin/ruff check src/

test:
	$(VENV)/bin/pytest

clean:
	rm -rf $(VENV) __pycache__ src/**/__pycache__ .pytest_cache dist
