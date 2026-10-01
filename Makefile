# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

PYTHON ?= python3
VARIANT ?= pro
COBOARD ?= 0
CONFIG ?= distribution.json
ASSEMBLER ?= z80asm
ZCC ?= zcc
COBOARD_SYSTEM ?= assets/boot/hdboot-coboard.trk
EMULATOR ?=
DEV_DIST ?= dist/dev
DEV_GAME_CACHE ?= $(DEV_DIST)/.game-cache
DEV_JOBS ?= 2
GAME_REPOS ?= ..
SITE_DIST ?= _site
WEB_BUILD ?= build/emulator-web
Z88DK_IMAGE ?= z88dk/z88dk@sha256:93f3c7c04486b300fdeccc600b48618e291ff1763aff608639fbfae0ee1623a5
EMSCRIPTEN_IMAGE ?= emscripten/emsdk@sha256:8847dad4171ebc8a53d9ae5cda86a2546ef5b2e68834c14dc1ba2b2962e125cc

ifeq ($(filter $(COBOARD),0 1),)
$(error COBOARD must be 0 or 1)
endif

BUILD = PYTHONPATH=src "$(PYTHON)" -m p2000c_disk.distribution
RAM_FLAG = $(if $(filter 1,$(COBOARD)),--coboard)
.DEFAULT_GOAL := help
.PHONY: help all dev dist pro pro-coboard menu menu-coboard release run verify trkdump test emulator emulator-web pinned-z88dk test-emulator menu-com site

help:
	@echo 'make pro                         Build the CP/M-prompt edition'
	@echo 'make pro-coboard                 Build CP/M with the CoPower RAM disk'
	@echo 'make menu                        Build the Navigator edition (requires Z88DK)'
	@echo 'make menu-coboard                Build Navigator with the CoPower RAM disk'
	@echo 'make all                         Build all four distribution editions'
	@echo 'make dev                         Build all editions with local game working trees'
	@echo 'make release                     Build all editions, tools, ZIPs and checksums'
	@echo 'make run                         Preview Navigator in the graphical emulator'
	@echo 'make run VARIANT=pro             Preview the CP/M prompt instead'
	@echo 'make verify VARIANT=pro          Verify one built edition; add COBOARD=1 if needed'
	@echo 'make menu-com                    Build standalone MENU.COM, MENU.BIN and MENU.DAT'
	@echo 'make trkdump                     Build the floppy capture utility'
	@echo 'make test                        Run the complete test suite'
	@echo 'make emulator                    Build the bundled headless C++ test core'
	@echo 'make emulator-web                Build WebAssembly (local Emscripten or Docker)'
	@echo 'make test-emulator               Run CP/M and CoPower execution tests'
	@echo 'make site                        Reproducibly build the browser site via Docker'
	@echo 'Add CONFIG=path.json             Select drive contents'

all: pro pro-coboard menu menu-coboard

dev:
	$(BUILD) dev --dist "$(DEV_DIST)" --games-root "$(GAME_REPOS)" --game-cache "$(DEV_GAME_CACHE)" --jobs "$(DEV_JOBS)" --config "$(CONFIG)" --assembler "$(ASSEMBLER)" --zcc "$(ZCC)" --coboard-system "$(COBOARD_SYSTEM)"

pro menu:
	$(MAKE) dist VARIANT=$@

pro-coboard:
	$(MAKE) dist VARIANT=pro COBOARD=1

menu-coboard:
	$(MAKE) dist VARIANT=menu COBOARD=1

dist:
	$(BUILD) dist --variant "$(VARIANT)" --config "$(CONFIG)" --assembler "$(ASSEMBLER)" --zcc "$(ZCC)" $(RAM_FLAG) $(if $(filter 1,$(COBOARD)),--coboard-system "$(COBOARD_SYSTEM)")

verify:
	$(BUILD) verify --variant "$(VARIANT)" $(RAM_FLAG)

run: VARIANT = menu
run:
	PYTHONPATH=src "$(PYTHON)" -m p2000c_disk.preview --variant "$(VARIANT)" --config "$(CONFIG)" --assembler "$(ASSEMBLER)" --zcc "$(ZCC)" $(RAM_FLAG) $(if $(filter 1,$(COBOARD)),--coboard-system "$(COBOARD_SYSTEM)") $(if $(EMULATOR),--emulator "$(EMULATOR)")

trkdump:
	$(BUILD) $@ --assembler "$(ASSEMBLER)"

release: all trkdump
	PYTHONPATH=src "$(PYTHON)" -m p2000c_disk.release

test:
	PYTHONPATH=src "$(PYTHON)" -m pytest

emulator:
	PYTHONPATH=src "$(PYTHON)" -m p2000c_disk.emulator

emulator-web:
	@if command -v emcmake >/dev/null 2>&1; then \
		emcmake cmake -S tools/emulator -B "$(WEB_BUILD)" -DCMAKE_BUILD_TYPE=Release; \
		cmake --build "$(WEB_BUILD)" --target p2000c-web --parallel; \
	elif command -v docker >/dev/null 2>&1; then \
		docker run --rm --user "$$(id -u):$$(id -g)" \
			-e HOME=/tmp -e EM_CACHE=/tmp/emscripten-cache \
			-v "$(CURDIR):/src" -w /src "$(EMSCRIPTEN_IMAGE)" sh -lc \
			'emcmake cmake -S tools/emulator -B "$(WEB_BUILD)" -DCMAKE_BUILD_TYPE=Release && cmake --build "$(WEB_BUILD)" --target p2000c-web --parallel'; \
	else \
		echo 'Emscripten or Docker is required for emulator-web.' >&2; exit 1; \
	fi

pinned-z88dk:
	@command -v docker >/dev/null 2>&1 || { echo 'Docker is required for reproducible Z88DK builds.' >&2; exit 1; }
	docker pull "$(Z88DK_IMAGE)"
	docker tag "$(Z88DK_IMAGE)" z88dk/z88dk:latest

test-emulator:
	PYTHONPATH=src "$(PYTHON)" -m pytest tests/test_coboard_emulator.py tests/test_trkdump_emulator.py tests/test_emulator.py

menu-com:
	PYTHONPATH=src "$(PYTHON)" -m p2000c_disk.menu --zcc "$(ZCC)" --assembler "$(ASSEMBLER)"

site: pinned-z88dk
	$(MAKE) menu ZCC="$(CURDIR)/tools/zcc"
	$(MAKE) emulator-web
	PYTHONPATH=src "$(PYTHON)" -m p2000c_disk.site --output "$(SITE_DIST)" \
		--media dist/menu --emulator "$(WEB_BUILD)/p2000c-web"
