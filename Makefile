.PHONY: install install-sys-deps run run-voice run-debug run-analysis lint test build clean

VENV    := .venv
PYTHON  := $(VENV)/bin/python
UV      := uv

DEVICE_IP   ?= 192.168.1.3
SESSION_DIR ?=

SDL2_PREFIX := $(shell brew --prefix sdl2 2>/dev/null)

install-sys-deps:
	brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf

install: install-sys-deps
	$(UV) venv $(VENV)
	CFLAGS="-I$(SDL2_PREFIX)/include -I$(SDL2_PREFIX)/include/SDL2" \
	LDFLAGS="-L$(SDL2_PREFIX)/lib" \
	$(UV) pip install -e ".[dev,voice,analysis,advisor]"

run run-voice:
	SIMRACING_DEVICE_IP=$(DEVICE_IP) $(PYTHON) -m simraceengineer.main --voice

run-debug:
	SIMRACING_DEVICE_IP=$(DEVICE_IP) $(PYTHON) -m simraceengineer.main --debug

run-analysis:
	$(PYTHON) -m simraceengineer.analysis.cli $(SESSION_DIR)

lint:
	$(VENV)/bin/ruff check src/

test:
	$(VENV)/bin/pytest

build:
	./build.sh

clean:
	rm -rf $(VENV) __pycache__ src/**/__pycache__ .pytest_cache dist build build_tmp
