##############################################################################
#
# Copyright (c) 2007-2009 Albert Cervera i Areny <albert@nan-tic.com>
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

import gettext
import os
import sys
import optparse

import Debug
from Settings import *
from Koo import Rpc

from PyQt4.QtCore import QDir, QUrl

def homeDirectory():
	return unicode(QDir.toNativeSeparators(QDir.homePath()))

def parseArguments(args):
	parser = optparse.OptionParser()
	parser.add_option("-d", "--database", dest="database", help=_("specify database"))
	parser.add_option("-c", "--config", dest="config", help=_("specify alternate config file"))
	parser.add_option("-u", "--url", dest="url", help=_("specify the server (ie. http://admin@localhost:8069)"))
	parser.add_option("", "--open-model", dest="open_model", default=None, help=_("specify model to be opened"))
	parser.add_option("", "--open-id", dest="open_id", default=None, help=_("specify id to be opened"))
	parser.add_option("", "--stylesheet", dest="stylesheet", default=None, help=_("specify stylesheet to apply"))
	parser.add_option("", "--pos-mode", action="store_true", default=None, dest="pos_mode", help=_("use POS (Point of Sales) mode"))
	parser.add_option("", "--enter-as-tab", action="store_true", default=None, dest="enter_as_tab", help=_("replace enter/return keys with tab hits"))
	parser.add_option("", "--disable-kde", action="store_true", default=None, dest="disable_kde", help=_("disable usage of KDE libraries if they are available"))
	parser.add_option("", "--debug", action="store_true", default=None, dest="debug", help=_("enable debug mode. Will show the crash dialog in all exceptions"))

	(options, arguments) = parser.parse_args(args)

	Settings.rcFile = options.config or os.environ.get('TERPRC') or os.path.join(homeDirectory(), '.koorc')
	Settings.loadFromFile()
	Settings.loadFromRegistry()

	# Allow URL to be specified in an environment variable so user password is not 
	# visible when listing running processes.
	if os.environ.get('KOO_URL'):
		Settings.setValue( 'login.url', os.environ.get('KOO_URL') )

	if options.url:
		Settings.setValue( 'login.url', options.url )
	if Settings.value( 'login.url' ):
		url = QUrl( Settings.value('login.url' ) )
	if not options.stylesheet is None:
		Settings.setValue( 'koo.stylesheet', options.stylesheet )
	if not options.pos_mode is None:
		Settings.setValue( 'koo.pos_mode', options.pos_mode )
	if not options.enter_as_tab is None:
		Settings.setValue( 'koo.enter_as_tab', options.enter_as_tab )
	if not options.debug is None:
		Settings.setValue( 'client.debug', options.debug )
	if not options.disable_kde is None:
		Settings.setValue( 'kde.enabled', False )
	if not options.database is None:
		Settings.setValue( 'login.db', options.database )
	if not options.open_model is None:
		Settings.setValue( 'open.model', options.open_model )
	if not options.open_id is None:
		Settings.setValue( 'open.id', options.open_id )
	return arguments

