#!/usr/bin/env make

SHELL := /bin/bash

DISTDIR := dist

PIPENV := pipenv
# PyInstaller cannot be installed using pip 19.1.
# See https://github.com/pypa/pip/issues/6163
PIP_REQUIRED_VERSION := '18.1'
VERSION := $(shell cat doc/VERSION)

NAME_VERSION := Subtitles-$(VERSION)
DMG_FILE := $(DISTDIR)/$(NAME_VERSION).dmg
DMG_SRCDIR := $(DISTDIR)/dmg_dir
# DMG_TEMP := $(shell mktemp)
APP_BUNDLE := $(DISTDIR)/Subtitles.app

EXE := $(DISTDIR)/Subtitles/Subtitles.exe
ZIP_FILE := $(DISTDIR)/$(NAME_VERSION).zip


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
	$(PIPENV) run pyinstaller -y Subtitles.pyinstaller.spec


package: build package-$(PLATFORM)



package-Darwin: $(DMG_FILE)

$(DMG_FILE):
	$(RM) -r "$(DMG_SRCDIR)"
	mkdir -p "$(DMG_SRCDIR)"
	mv "$(APP_BUNDLE)" "$(DMG_SRCDIR)"
	hdiutil create "$(DMG_FILE)" \
		-srcfolder "$(DMG_SRCDIR)" \
		-format UDBZ \
		-volname "$(NAME_VERSION)"
	$(RM) -r "$(DMG_SRCDIR)"



package-Windows: $(ZIP_FILE)

$(ZIP_FILE): $(DISTDIR)
	$(RM) $(ZIP_FILE)
	cd $(DISTDIR) && zip -dd -9 -o -r $(NAME_VERSION).zip Subtitles >/dev/null
	@echo "ZIP File $(ZIP_FILE) created."


package-Linux:
	@ls -la $(DISTDIR)


depends: depends-$(PLATFORM) pip-version Pipfile.lock


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
	$(PIPENV) update


depends-Windows:

depends-Linux:

depends-Darwin:


# release: package


clean:
	$(RM) -r build dist


.PHONY: err diag clean build
err: ; $(ERROR)
