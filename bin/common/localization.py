import paths

def initializeTranslations():
	import locale
	import gettext

	name = 'ktiny'
	directory = paths.searchFile( 'l10n' )

	locale.setlocale(locale.LC_ALL, '')
	gettext.bindtextdomain(name, directory)
	gettext.textdomain(name)
	gettext.install(name, directory, unicode=1)

def initializeQtTranslations():
	from PyQt4.QtCore import QTranslator, QCoreApplication, QLocale
	translator = QTranslator( QCoreApplication.instance() )
	language = str(QLocale.system().name())
	# First we try to load the file with the same system language name 
	# Usually in $LANG and looks something like ca_ES, de_DE, etc.
	file = paths.searchFile( language + '.qm', 'l10n' )
	if not file:
		# If the first step didn't work try to remove country
		# information and try again.
		language = language.split('_')[0]
		file = paths.searchFile( language + '.qm', 'l10n' )
	if not file:
		# If no translation files were found, don't crash
		# but continue silently.
		return
	translator.load( file )
	QCoreApplication.instance().installTranslator( translator )

