#!/usr/bin/env make

SHELL := /bin/bash

DISTDIR := dist

PIPENV := pipenv
# PyInstaller cannot be installed using pip 19.1.
# See https://github.com/pypa/pip/issues/6163
PIP_REQUIRED_VERSION := '18.1'
VERSION := $(shell cat doc/VERSION)
GIT_COMMIT := $(shell git log --pretty=format:'%h' -n 1)

CREATE_DMG := node_modules/create-dmg/cli.js

NAME := Subtitles
NAME_VERSION = $(NAME)-$(VERSION)
DMG_FILE = $(DISTDIR)/$(NAME_VERSION).dmg
DMG_SRCDIR = $(DISTDIR)/dmg_dir
# DMG_TEMP := $(shell mktemp)
APP_BUNDLE = $(DISTDIR)/Subtitles.app

EXE := $(DISTDIR)/Subtitles/Subtitles.exe
ZIP_FILE := $(DISTDIR)/$(NAME_VERSION).zip
ZIP_FILE_WINDOWS := $(DISTDIR)/$(NAME_VERSION)-Windows.zip
ZIP_FILE_LINUX := $(DISTDIR)/$(NAME_VERSION)-Linux.zip


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


all: depends build package


diag:
	@echo "Platform: $(PLATFORM)"
	@echo "Python: $(PYTHON), version: $(shell $(PYTHON) --version)"
	@echo "pip: $(PIP), version: $(shell $(PIP) --version)"
	@echo "PIP_INSTALL=$(PIP_INSTALL)"


build:
	@if [ -n "$(TRAVIS_COMMIT)" ]; then \
		echo "$(TRAVIS_COMMIT)" > doc/VERSION.commit; \
	fi
	@if [ -n "${TRAVIS_APP_HOST}" ]; then \
		echo "${TRAVIS_APP_HOST}" > doc/VERSION.build_host; \
	fi
	@if [ -n "${TRAVIS_BUILD_NUMBER}" ]; then \
		echo "${TRAVIS_BUILD_NUMBER}" > doc/VERSION.build_number; \
	fi
	$(PIPENV) run pyinstaller -y Subtitles.pyinstaller.spec


package: build package-$(PLATFORM)



package-Darwin: $(DMG_FILE)

$(DMG_FILE):
	@if $(CREATE_DMG) --overwrite "$(APP_BUNDLE)" "$(DISTDIR)" \
		| grep 'No usable identity found'; then \
		if [ ! -f "$(DISTDIR)/$(NAME) $(VERSION).dmg" ]; then \
			echo "Code signing failed (normal), but DMG not created."; \
			exit 1; \
		fi ; \
		echo "Warning: Unable to code sign DMG"; \
	fi
	mv "$(DISTDIR)/$(NAME) $(VERSION).dmg" "$(DISTDIR)/$(NAME_VERSION).dmg"




package-Windows: $(ZIP_FILE_WINDOWS)

$(ZIP_FILE_WINDOWS): $(ZIP_FILE)
	mv "$(ZIP_FILE)" "$(ZIP_FILE_WINDOWS)"


$(ZIP_FILE): $(DISTDIR)
	$(RM) $(ZIP_FILE)
	cd $(DISTDIR) && zip -dd -9 -o -r $(NAME_VERSION).zip Subtitles >/dev/null
	@echo "ZIP File $(ZIP_FILE) created."


package-Linux: $(ZIP_FILE_LINUX)

$(ZIP_FILE_LINUX): $(ZIP_FILE)
	mv "$(ZIP_FILE)" "$(ZIP_FILE_LINUX)"


depends: depends-$(PLATFORM) pip-version Pipfile.lock

depends-force:
	touch Pipfile
	$(MAKE) depends


pip-version:
	$(eval PIP_CUR_MAJOR_VERSION := $(shell $(PIPENV) run pip --version | cut -d' ' -f2 | cut -d. -f1))
	$(eval PIP_REQ_MAJOR_VERSION := $(shell echo $(PIP_REQUIRED_VERSION) | cut -d. -f1))
	@if [ "$(PIP_CUR_MAJOR_VERSION)" == "$(PIP_REQ_MAJOR_VERSION)" ]; then \
		echo "pip $(PIP_CUR_MAJOR_VERSION) installed, no down- or upgrade needed" ; \
	else \
		echo "pip must be changed to $(PIP_REQUIRED_VERSION)" ; \
		$(PIPENV) run python -m pip install pip==$(PIP_REQUIRED_VERSION); \
	fi

Pipfile.lock: Pipfile
	$(PIPENV) sync


depends-Windows:

depends-Linux:

depends-Darwin:


# release: package


clean:
	$(RM) -r build dist


.PHONY: err diag clean build depends depends-$(PLATFORM) pip-version
err: ; $(ERROR)
