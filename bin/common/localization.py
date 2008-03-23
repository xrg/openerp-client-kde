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
	translator.load( paths.searchFile( str(QLocale.system().name()) , 'l10n' ) )
	QCoreApplication.instance().installTranslator( translator )

