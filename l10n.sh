#!/bin/bash

UI_FILES=$(find bin/ui -name "*.ui")
PYTHON_FILES=$(find bin -name "*py")
PYTHONC_FILES=$(find -name "*pyc")
LANGS="ca_ES de es fr hu it pt ro ru sv uk zh al cs"
DIR="bin/l10n"

# Extract strings with get text from python files
xgettext -k_ -kN_ -o $DIR/ktiny.pot $PYTHON_FILES

# Merge template with existing translations
echo "Merging..."
for x in $LANGS; do
	if [ -f $DIR/$x.po ]; then
		msgmerge $DIR/$x.po $DIR/ktiny.pot -o $DIR/$x.po
	else
		cp $DIR/ktiny.pot $DIR/$x.po
	fi
	pylupdate4 $UI_FILES -ts $DIR/$x.ts
done
rmdir $DIR/LC_MESSAGES 2>/dev/null

# Compile 
echo "Compiling..."
for x in $LANGS; do
	mkdir $DIR/$x 2>/dev/null
	mkdir $DIR/$x/LC_MESSAGES 2>/dev/null
	msgfmt $DIR/$x.po -o $DIR/$x/LC_MESSAGES/ktiny.mo;
	lrelease $DIR/$x.ts -qm $DIR/$x.qm
done
