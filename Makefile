PYTHON ?= python3
VARIANT ?= pro
COBOARD ?= 0
CONFIG ?= distribution.json
ASSEMBLER ?= z80asm
ZCC ?= zcc
COBOARD_SYSTEM ?= assets/boot/hdboot-coboard.trk
EMULATOR ?=

ifeq ($(filter $(COBOARD),0 1),)
$(error COBOARD must be 0 or 1)
endif

BUILD = PYTHONPATH=src "$(PYTHON)" -m p2000c_disk.distribution
RAM_FLAG = $(if $(filter 1,$(COBOARD)),--coboard)
.DEFAULT_GOAL := help
.PHONY: help all dist pro pro-coboard menu menu-coboard release run verify trkdump test emulator test-emulator menu-com

help:
	@echo 'make pro                         Build the CP/M-prompt edition'
	@echo 'make pro-coboard                 Build CP/M with the CoPower RAM disk'
	@echo 'make menu                        Build the Navigator edition (requires Z88DK)'
	@echo 'make menu-coboard                Build Navigator with the CoPower RAM disk'
	@echo 'make all                         Build all four distribution editions'
	@echo 'make release                     Build all editions, tools, ZIPs and checksums'
	@echo 'make run                         Preview Navigator in the graphical emulator'
	@echo 'make run VARIANT=pro             Preview the CP/M prompt instead'
	@echo 'make verify VARIANT=pro          Verify one built edition; add COBOARD=1 if needed'
	@echo 'make menu-com                    Build standalone MENU.COM and MENU.DAT'
	@echo 'make trkdump                     Build the floppy capture utility'
	@echo 'make test                        Run the complete test suite'
	@echo 'make emulator                    Build the bundled headless C++ test core'
	@echo 'make test-emulator               Run CP/M and CoPower execution tests'
	@echo 'Add CONFIG=path.json             Select drive contents'

all: pro pro-coboard menu menu-coboard

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

test-emulator:
	PYTHONPATH=src "$(PYTHON)" -m pytest tests/test_coboard_emulator.py tests/test_trkdump_emulator.py tests/test_emulator.py

menu-com:
	PYTHONPATH=src "$(PYTHON)" -m p2000c_disk.menu --zcc "$(ZCC)"
