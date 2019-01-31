#!/usr/bin/env make

PIPENV := pipenv
# PyInstaller cannot be installed using pip 19.1.
# See https://github.com/pypa/pip/issues/6163
PIP_VERSION := '18.1'


PLATFORM := $(shell uname -s)
ifneq (,$(findstring MINGW, $(PLATFORM)))
	PLATFORM := Windows
else
	ifneq (,$(findstring MSYS_NT, $(PLATFORM)))
		PLATFORM := Windows
	endif
endif

ifeq ($(PLATFORM),Windows)
	PYTHON := python3
	PIP := pip3
	PIP_INSTALL := "$(PIP) install"
else
	ifeq ($(PLATFORM),Linux)
		PYTHON := python
		PIP := pip
		PIP_INSTALL := "$(PIP) install"
	else
		ifeq ($(PLATFORM),Darwin)
			PYTHON := python
			PIP := pip
			PIP_INSTALL := "$(PIP) install"
		else
			ERROR = $(error "Unsupported platform '$(PLATFORM)'")
		endif
	endif
endif


all: build release


diag:
	@echo "Platform: $(PLATFORM)"
	@echo "Python: $(PYTHON), version: $(shell $(PYTHON) --version)"
	@echo "pip: $(PIP), version: $(shell $(PIP) --version)"
	@echo "PIP_INSTALL=$(PIP_INSTALL)"


build: depends package


package:
	@echo "PWD: $(shell pwd)"
	ls -la
	@echo "PATH: $(shell echo $$PATH)"
	$(PIPENV) run pyinstaller -y Subtitles.pyinstaller.spec


depends: depends-$(PLATFORM) Pipfile.lock
	$(PIPENV) run python -m pip install pip==$(PIP_VERSION)
	$(PIPENV) run $(PIP) --version
	$(PIPENV) update


Pipfile.lock: Pipfile


release: Subtitles.pyinstaller.spec
	

depends-Windows:
	choco install python3 --params "/PrependPath=1"

depends-Linux:

depends-Darwin:


clean:
	$(RM) -r build dist


.PHONY: err diag clean
err: ; $(ERROR)
