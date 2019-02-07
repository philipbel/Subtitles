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
APPDIR := $(DISTDIR)/$(NAME_VERSION).AppDir
APPIMAGE := $(DISTDIR)/$(NAME_VERSION).AppImage
BUILD_TIMESTAMP := $(DISTDIR)/build.timestamp
DESKTOP_FILE_IN := resources/linux/$(NAME).desktop
DESKTOP_FILE_OUT := $(APPDIR)/$(NAME).desktop
APPRUN_IN := resources/linux/AppRun.sh
APPRUN_OUT := $(APPDIR)/AppRun

PLATFORM := $(shell uname -s)
ifneq (,$(findstring MINGW, $(PLATFORM)))
	PLATFORM := Windows
else
	ifneq (,$(findstring MSYS_NT, $(PLATFORM)))
		PLATFORM := Windows
	endif
endif

ifeq ($(PLATFORM),Linux)
	ifeq ($(APPIMAGETOOL),)
		APPIMAGETOOL := appimagetool
	endif
	ifeq (,$(shell which $(APPIMAGETOOL)))
		$(error "You must have appimagetool in your PATH or set the APPIMAGETOOL environment variable")
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



build: $(BUILD_TIMESTAMP)

$(BUILD_TIMESTAMP):
	if [ -n "${TRAVIS_COMMIT}" ]; then \
		GIT_COMMIT="${TRAVIS_COMMIT}"; \
	else \
		GIT_COMMIT="$(shell git log --pretty=format:'%h' -n 1)"; \
	fi; \
	if [ -n "$(GIT_COMMIT)" ]; then	\
		echo "$(GIT_COMMIT)" > doc/VERSION.commit; \
	fi

	echo "$(shell uname -n -r -m -o)" > doc/VERSION.build_host

	if [ -n "${TRAVIS_BUILD_NUMBER}" ]; then \
		echo "${TRAVIS_BUILD_NUMBER}" > doc/VERSION.build_number; \
	fi

	$(PIPENV) run pyinstaller -y Subtitles.pyinstaller.spec
	touch $(BUILD_TIMESTAMP)


package: package-$(PLATFORM)



package-Darwin: $(DMG_FILE)

$(DMG_FILE): $(BUILD_TIMESTAMP)
	@if $(CREATE_DMG) --overwrite "$(APP_BUNDLE)" "$(DISTDIR)" \
		| grep 'No usable identity found'; then \
		if [ ! -f "$(DISTDIR)/$(NAME) $(VERSION).dmg" ]; then \
			@echo "Code signing failed (normal), but DMG not created."; \
			exit 1; \
		fi ; \
		@echo "Warning: Unable to code sign DMG"; \
	fi
	mv "$(DISTDIR)/$(NAME) $(VERSION).dmg" "$(DISTDIR)/$(NAME_VERSION).dmg"


package-Windows: $(ZIP_FILE_WINDOWS)

$(ZIP_FILE_WINDOWS): $(ZIP_FILE)
	mv "$(ZIP_FILE)" "$(ZIP_FILE_WINDOWS)"


$(ZIP_FILE): $(BUILD_TIMESTAMP)
	# $(RM) $(ZIP_FILE)
	cd $(DISTDIR) && zip -dd -9 -o -r $(NAME_VERSION).zip $(NAME) >/dev/null
	@echo "ZIP File $(ZIP_FILE) created."


package-Linux: $(ZIP_FILE_LINUX) $(APPIMAGE)

$(ZIP_FILE_LINUX): $(ZIP_FILE)
	mv "$(ZIP_FILE)" "$(ZIP_FILE_LINUX)"

$(APPIMAGE): $(APPDIR)-dir $(APPDIR)
	$(APPIMAGETOOL) $(APPDIR) $(APPIMAGE)

$(APPDIR)-dir:
	$(RM) -r $(APPDIR)
	# mkdir -p $(APPDIR)/usr/bin/
	mkdir -p $(APPDIR)/usr/lib/Subtitles/


$(APPDIR): $(BUILD_TIMESTAMP) $(DESKTOP_FILE_OUT) $(APPRUN_OUT)
	cp -r $(DISTDIR)/Subtitles/* $(APPDIR)/usr/lib/Subtitles
	chmod +x $(APPDIR)/usr/lib/Subtitles/Subtitles
	cp $(APPDIR)/usr/lib/Subtitles/Subtitles.png $(APPDIR)/


$(APPRUN_OUT): $(APPRUN_IN)
	cp -r $(APPRUN_IN) $(APPRUN_OUT)
	chmod +x $(APPRUN_OUT)

$(DESKTOP_FILE_OUT): $(DESKTOP_FILE_IN)
	cp $(DESKTOP_FILE_IN) $(DESKTOP_FILE_OUT)


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



clean:
	$(RM) -r build dist


.PHONY: err diag clean build depends depends-$(PLATFORM) pip-version
err: ; $(ERROR)
