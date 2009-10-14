# Makefile for language

UI_FILES:=$(shell find Koo/ui -name "*.ui")
PYTHON_FILES:=$(shell find Koo -name "*.py")
PYTHONC_FILES:=$(shell find Koo -name "*.pyc")
LANGS = ca de el es fr hu it pt ro ru sv uk zh al cs
QT_LANGS = ca de el es fr
DIR := Koo/l10n

ALL_MOFILES = ${LANGS:%=${DIR}/%/LC_MESSAGES/koo.mo}
TSFILES = ${QT_LANGS:%=${DIR}/%.ts}

all: mofiles qmfiles
	echo "Message catalogs compiled!"
	

${DIR}/koo.pot: ${PYTHON_FILES}
	# Extract strings with get text from python files
	@xgettext -k_ -kN_ -o $@ $^

mofiles: pofiles ${ALL_MOFILES}

pofiles: ${LANGS:%=${DIR}/%.po}

qmfiles: ${TSFILES} ${QT_LANGS:%=${DIR}/%.qm}

${DIR}/%.po: ${DIR}/koo.pot
	@if [ -e $@ ] ; then \
		msgmerge -U $@ $< ;\
	else echo "Catalog $@ is missing." ;\
	     echo "Please create, or 'make initpofiles' ." ;\
	fi

# Initialize missing po files
initpofiles: ${DIR}/koo.pot
	@pushd ${DIR} ;\
	for LANG in ${LANGS} ; do \
		[ -e $$LANG.po ] && continue ; \
		msginit --no-translator --no-wrap \
			-l $$LANG \
			-o $$LANG.po -i koo.pot ;\
	done ; popd

${DIR}/%/LC_MESSAGES/koo.mo: ${DIR}/%.po
	[ -d $(dir $@) ] || mkdir -p $(dir $@)
	@msgfmt -o $@ $<


# Run lupdate only once and produce all langs
${TSFILES}: ${UI_FILES}
	@pylupdate4 ${UI_FILES} -ts ${TSFILES}

${DIR}/%.qm: ${DIR}/%.ts
	lrelease $< -qm $@

clean:
	rm -f ${QT_LANGS:%=${DIR}/%.qm}
	rm -f ${LANGS:%=${DIR}/%.mo}
	find ${DIR} -name '*.mo' -delete
	find ${DIR} -type d -empty -delete

#eof
