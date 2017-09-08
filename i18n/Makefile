#!/usr/bin/make -f

PROJECT = odfinder

GETTEXT = /usr/bin/xgettext
MSGMERGE = /usr/bin/msgmerge

PO = $(shell find . -name '*.po' -print | sed -e 's!./!!g')

update-po:
	$(GETTEXT) -f POT_PY_FILES -L python -d $(PROJECT) -o $(PROJECT).pot
	$(GETTEXT) -f POT_UI_FILES -L Glade -d $(PROJECT) -j -o $(PROJECT).pot
	for lang in $(PO); do $(MSGMERGE) -U $$lang $(PROJECT).pot; done
