#!/usr/bin/env make

PIPENV := pipenv
# PyInstaller cannot be installed using pip 19.1.
# See https://github.com/pypa/pip/issues/6163
PIP_VERSION := '18.1'
VERSION := $(shell cat doc/VERSION)

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


package: package-$(PLATFORM)

DISTDIR := dist
DMG_NAME := Subtitles-$(VERSION)
DMG_FILE := $(DISTDIR)/$(DMG_NAME).dmg
DMG_SRCDIR := $(DISTDIR)/dmg_dir
# DMG_TEMP := $(shell mktemp)
APP_BUNDLE := $(DISTDIR)/Subtitles.app

package-Darwin: $(DMG_FILE)

$(DMG_FILE): $(APP_BUNDLE)
	$(RM) -r "$(DMG_SRCDIR)"
	mkdir -p "$(DMG_SRCDIR)"
	mv "$(APP_BUNDLE)" "$(DMG_SRCDIR)"
	hdiutil create "$(DMG_FILE)" \
		-srcfolder "$(DMG_SRCDIR)" \
		-format UDBZ \
		-volname "$(DMG_NAME)"
	$(RM) -r "$(DMG_SRCDIR)"


$(APP_BUNDLE): Subtitles.pyinstaller.spec
	$(PIPENV) run pyinstaller -y Subtitles.pyinstaller.spec


depends: depends-$(PLATFORM)
	$(PIPENV) run python -m pip install pip==$(PIP_VERSION)
	$(PIPENV) update


depends-Windows:

depends-Linux:

depends-Darwin:


clean:
	$(RM) -r build dist


.PHONY: err diag clean
err: ; $(ERROR)
