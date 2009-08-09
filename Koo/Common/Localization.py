##############################################################################
#
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import Paths
import os

## @brief Initializes gettext translation system.
def initializeTranslations(language=None):
	import locale
	import gettext

	name = 'koo'
	try:
		locale.setlocale(locale.LC_ALL, '')
	except:
		# If locale is not supported just continue
		# with default language
		print "Warning: Unsupported locale." 

	if not language:
		language, encoding = locale.getdefaultlocale()
		if not language:
			language = 'C'

	# Set environment variables otherwise it doesn't properly
	# work on windows
	os.environ.setdefault('LANG', language)
	os.environ.setdefault('LANGUAGE', language)

	# First of all search the files in the l10n directory (in case Koo was
	# not installed in the system).
	directory = Paths.searchFile( 'l10n' )
	if directory:
		try:
			lang = gettext.translation(name, directory, fallback=False)
		except:
			directory = None

	if not directory:
		# If the first try didn't work try to search translation files
		# in standard directories 'share/locale'
		directory = Paths.searchFile( os.path.join('share','locale') )
		lang = gettext.translation(name, directory, fallback=True)

	lang.install(unicode=1)

## @brief Initializes Qt translation system.
def initializeQtTranslations(language=None):
	from PyQt4.QtCore import QTranslator, QCoreApplication, QLocale
	if not language:
		language = str(QLocale.system().name())
	print "SETTING QT: ", language

	# First we try to load the file with the same system language name 
	# Usually in $LANG and looks something like ca_ES, de_DE, etc.
	file = Paths.searchFile( '%s.qm' % language, 'l10n' )
	if not file:
		# If the first step didn't work try to remove country
		# information and try again.
		language = language.split('_')[0]
		file = Paths.searchFile( '%s.qm' % language, 'l10n' )

	# If no translation files were found, don't crash
	# but continue silently.
	if file:
		translator = QTranslator( QCoreApplication.instance() )
		translator.load( file )
		QCoreApplication.instance().installTranslator( translator )

	# First we try to load the file with the same system language name 
	# Usually in $LANG and looks something like ca_ES, de_DE, etc.
	file = Paths.searchFile( 'qt_%s.qm' % language, 'l10n' )
	if not file:
		# If the first step didn't work try to remove country
		# information and try again.
		language = language.split('_')[0]
		file = Paths.searchFile( 'qt_%s.qm' % language, 'l10n' )
	# If no translation files were found, don't crash
	# but continue silently.
	if file:
		translator = QTranslator( QCoreApplication.instance() )
		translator.load( file )
		QCoreApplication.instance().installTranslator( translator )

