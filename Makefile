.PHONY: install install-sys-deps run run-debug lint test clean

VENV    := .venv
PYTHON  := $(VENV)/bin/python
UV      := uv

PS5_IP ?= 192.168.1.100

SDL2_PREFIX := $(shell brew --prefix sdl2 2>/dev/null)

install-sys-deps:
	brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf

install: install-sys-deps
	$(UV) venv $(VENV)
	CFLAGS="-I$(SDL2_PREFIX)/include -I$(SDL2_PREFIX)/include/SDL2" \
	LDFLAGS="-L$(SDL2_PREFIX)/lib" \
	$(UV) pip install -e ".[dev]"

run:
	$(PYTHON) -m simracing.main --ps5-ip $(PS5_IP)

run-debug:
	$(PYTHON) -m simracing.main --ps5-ip $(PS5_IP) --debug

lint:
	$(VENV)/bin/ruff check src/

test:
	$(VENV)/bin/pytest

clean:
	rm -rf $(VENV) __pycache__ src/**/__pycache__ .pytest_cache dist
