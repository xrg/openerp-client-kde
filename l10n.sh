#!/bin/bash

function ts2po
{
	ts=$1
	po=$2

	lconvert $DIR/$ts --output-format po -o $DIR/$po

	# Remove duplicates from qt-koo.pot
	./remove-duplicates.pl $DIR/$po
	# Change header of qt-koo.pot: otherwise launchpad tries to process it using UTF-8 and doesn't work
	perl -pi -e "s/X-Virgin-Header: remove this line if you change anything in the header./Project-Id-Version: PACKAGE VERSION\\\nReport-Msgid-Bugs-To: \\\nPOT-Creation-Date: 2009-07-28 00:00+0200\\\nPO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\\nLast-Translator: FULL NAME <EMAIL@ADDRESS>\\\nLanguage-Team: LANGUAGE <LL@li.org>\\\nMIME-Version: 1.0\\\nContent-Type: text\/plain; charset=iso-8859-1/" Koo/l10n/$po
}

function po2ts
{
	po=$1
	ts=$2
	lconvert $DIR/$po --output-format ts -o $DIR/$ts
}

UI_FILES=$(find Koo/ui -name "*.ui")
PYTHON_FILES=$(find Koo -name "*py")
PYTHONC_FILES=$(find -name "*pyc")
LANGS=$(find Koo/l10n/ -name "*.po" -printf "%f\n" | grep -v "qt-" | cut -d "." -f 1)
QT_LANGS=$(find Koo/l10n/ -name "qt-*.po" -printf "%f\n" | cut -d "." -f 1 | cut -d "-" -f 3)
DIR="Koo/l10n"

# Extract strings with get text from python files
echo "Extracting strings from python files with xgettext"
xgettext -k_ -kN_ -o $DIR/koo.pot $PYTHON_FILES
echo "Extracting strings from ui files with pylupdate4"
pylupdate4 $UI_FILES -ts $DIR/koo.ts
ts2po koo.ts qt-koo.pot

# Merge template with existing translations
echo "Converting qt-koo*.po files to .ts and then compiling to .qm"
echo $QT_LANGS
for x in $QT_LANGS; do
	po2ts qt-koo-$x.po qt_$x.ts
	lrelease $DIR/qt_$x.ts -qm $DIR/qt_$x.qm
done

#for x in $LANGS; do
	#if [ -f $DIR/$x.po ]; then
		#msgmerge $DIR/$x.po $DIR/koo.pot -o $DIR/$x.po
	#else
		#cp $DIR/koo.pot $DIR/$x.po
	#fi
	#pylupdate4 $UI_FILES -ts $DIR/$x.ts
	#ts2po $x.ts qt-koo_$x.po
#done
rmdir $DIR/LC_MESSAGES 2>/dev/null

# Compile 
echo "Compiling .po files..."
for x in $LANGS; do
	mkdir $DIR/$x 2>/dev/null
	mkdir $DIR/$x/LC_MESSAGES 2>/dev/null
	msgfmt $DIR/$x.po -o $DIR/$x/LC_MESSAGES/koo.mo;
done
