#!/bin/bash

UI_FILES=$(find Koo/ui -name "*.ui")
PYTHON_FILES=$(find Koo -name "*py")
PYTHONC_FILES=$(find -name "*pyc")
LANGS="ca_ES de_DE es_ES fr hu it pt ro ru sv uk zh al cs"
DIR="Koo/l10n"

# Extract strings with get text from python files
xgettext -k_ -kN_ -o $DIR/koo.pot $PYTHON_FILES
pylupdate4 $UI_FILES -ts $DIR/koo.ts
lconvert $DIR/koo.ts --output-format po -o $DIR/qt-koo.pot

# Remove duplicates from qt-koo.pot
./remove-duplicates.pl
# Change header of qt-koo.pot: otherwise launchpad tries to process it using UTF-8 and doesn't work
perl -pi -e "s/X-Virgin-Header: remove this line if you change anything in the header./Project-Id-Version: PACKAGE VERSION\\\nReport-Msgid-Bugs-To: \\\nPOT-Creation-Date: 2009-07-28 00:00+0200\\\nPO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\\nLast-Translator: FULL NAME <EMAIL@ADDRESS>\\\nLanguage-Team: LANGUAGE <LL@li.org>\\\nMIME-Version: 1.0\\\nContent-Type: text\/plain; charset=iso-8859-1/" Koo/l10n/qt-koo.pot

# Merge template with existing translations
echo "Merging..."
for x in $LANGS; do
	if [ -f $DIR/$x.po ]; then
		msgmerge $DIR/$x.po $DIR/koo.pot -o $DIR/$x.po
	else
		cp $DIR/koo.pot $DIR/$x.po
	fi
	pylupdate4 $UI_FILES -ts $DIR/$x.ts
	lconvert $DIR/$x.ts -o $DIR/qt-$x.po
done
rmdir $DIR/LC_MESSAGES 2>/dev/null

# Compile 
echo "Compiling..."
for x in $LANGS; do
	mkdir $DIR/$x 2>/dev/null
	mkdir $DIR/$x/LC_MESSAGES 2>/dev/null
	msgfmt $DIR/$x.po -o $DIR/$x/LC_MESSAGES/koo.mo;
	lrelease $DIR/$x.ts -qm $DIR/$x.qm
done
