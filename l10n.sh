#!/bin/bash

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

lconvert $DIR/koo.ts --output-format po -o $DIR/qt-koo.pot


# Merge template with existing translations

echo "Converting qt-koo*.po files to .ts and then compiling to .qm"
echo $QT_LANGS

for x in $QT_LANGS; do
	echo $x
	#utf="no"
	#po2ts qt-koo-$x.po qt_$x.ts $utf
	if [ -f $DIR/qt-koo-$x.po ]; then
		msgmerge $DIR/qt-koo-$x.po $DIR/qt-koo.pot -o $DIR/qt_koo-$x.po
	else
		cp $DIR/qt-koo.pot $DIR/qt-koo-$x.po
	fi
    lconvert $DIR/qt-koo-$x.po --output-format ts -o $DIR/qt_$x.ts
	lrelease $DIR/qt_$x.ts -qm $DIR/qt_$x.qm
done

rmdir $DIR/LC_MESSAGES 2>/dev/null


# Compile 

echo "Compiling .po files..."

for x in $LANGS; do
	mkdir $DIR/$x 2>/dev/null
	mkdir $DIR/$x/LC_MESSAGES 2>/dev/null
	msgfmt $DIR/$x.po -o $DIR/$x/LC_MESSAGES/koo.mo;
done
