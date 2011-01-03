##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

import ConfigParser
import os
import sys
from Koo import Rpc
import Debug
from PyQt4.QtCore import QDir, QUrl

## @brief The ConfigurationManager class handles Koo settings information. 
# Those settings can be specified in the command line, .koorc configuration file
# or koo server module.
class Settings(object):
	rcFile = False
	options = {
		'login.db': 'test',
		'login.url': 'http://admin@localhost:8069',
		'path.share': os.path.join(sys.prefix, 'share/Koo/'),
		'path.pixmaps': os.path.join(sys.prefix, 'share/pixmaps/Koo/'),
		'path.ui': os.path.join(sys.prefix, 'share/Koo/ui'), 
		'tip.autostart': True,
		'tip.position': 0,
		'client.default_path': os.path.expanduser('~'),
		'client.language': False,
		'client.debug': False,
		'logging.level': 30, # hard code the logging.WARN value
		'logging.uic_debug': False,
		'koo.print_directly': False,
		'koo.stylesheet' : '',
		'koo.tabs_position' : 'top',
		'koo.tabs_closable' : True,
		'koo.show_toolbar' : True,
		'koo.sort_mode' : 'all_items',
		'koo.pos_mode' : False,
		'koo.enter_as_tab' : False,
		'kde.enabled' : True,
		'koo.attachments_dialog' : False,
		'client.devel_mode': False,
		'koo.load_on_open' : True,
		'SerialScanner.enable': False,
		'koo.smtp_server' : 'mail.nan-tic.com',
		'koo.smtp_from' : 'koo@nan-tic.com',
		'koo.smtp_backtraces_to' : 'backtraces@nan-tic.com',
	}

	## @brief Stores current settings in the appropiate config file.
	@staticmethod
	def saveToFile():
		if not Settings.rcFile:
			# If no file was specified we try to read it from environment 
			# variable o standard path
			Settings.rcFile = os.environ.get('TERPRC') or os.path.join(unicode(QDir.toNativeSeparators(QDir.homePath())), '.koorc')
		try:
			parser = ConfigParser.ConfigParser()
			sections = {}
			for option in Settings.options.keys():
				if not len(option.split('.'))==2:
					continue

				optionSection, optionName = option.split('.')

				if not parser.has_section(optionSection):
					parser.add_section(optionSection)

				# Do not store 'open' settings unless the 'always' flag is
				# present.
				value = Settings.options[option]
				if optionSection == 'open' and not Settings.value('open.always'):
					value = ''

				parser.set(optionSection, optionName, value)

			# Set umask='077' to ensure file permissions used are '600'.
			# This way we can store passwords and other information safely.
			oldUmask = os.umask(63)
			f = open(Settings.rcFile, 'wb')
			try:
				parser.write( f )
			except:
				Debug.warning( 'Unable to write config file %s !' % Settings.rcFile )
			finally:
				f.close()
			os.umask(oldUmask)
		except:
			Debug.warning( 'Unable to write config file %s !' % Settings.rcFile )
		return True

	## @brief Loads settings from the appropiate config file.
	@staticmethod
	def loadFromFile():
		if not Settings.rcFile:
			# If no file was specified we try to read it from environment 
			# variable o standard path
			Settings.rcFile = os.environ.get('TERPRC') or os.path.join(unicode(QDir.toNativeSeparators(QDir.homePath())), '.koorc')
		try:
			if not os.path.isfile(Settings.rcFile):
				Settings.save()
				return False

			p = ConfigParser.ConfigParser()
			p.read([Settings.rcFile])
			for section in p.sections():
				for (name,value) in p.items(section):
					if value=='True' or value=='true':
						value = True
					if value=='False' or value=='false':
						value = False
					Settings.options[section+'.'+name] = value
		except Exception, e:
			Debug.warning( 'Unable to read config file %s !' % Settings.rcFile )
		return True

	## @brief Loads settings from Windows registry.
	@staticmethod
	def loadFromRegistry():
		if os.name != 'nt':
			return

		languages = {
			'1027': 'ca',
			'1031': 'de',
			'1033': 'en',
			'1034': 'es',
			'1040': 'it',
		}
			
		import _winreg
		key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Software\Koo")
		value, value_type = _winreg.QueryValueEx(key, "Language")
		Settings.options['client.language'] = languages.get(value, False)

	## @brief Sets the value for the given key.
	@staticmethod
	def setValue(key, value):
		Settings.options[key]=value

	## @brief Returns the value for the given key.
	#
	# If defaultValue parameter is given, defaultValue is returned if the key does not exist.
	# If type is given, it will convert the value to the given type.
	@staticmethod
	def value(key, defaultValue=None, toType=None):
		value = Settings.options.get(key, defaultValue)
		if toType == int:
			return int( value )
		return value

	## @brief Returns the value associated with the given key. If the key has no valu
	# returns defaultValue
	@staticmethod
	def get(key, defaultValue=None):
		return Settings.options.get(key, defaultValue)

	## @brief Tries to load settings from koo server module.
	# If the module is not installed, no exception or error is thrown.
	@staticmethod
	def loadFromServer():
		try:
			settings = Rpc.session.call( '/object', 'execute', 'nan.koo.settings', 'get_settings' )
		except:
			settings = {}
		new_settings = {}
		for key, value in settings.iteritems():
			if key != 'id':
				new_settings[ 'koo.%s' % key ] = value
		Settings.options.update( new_settings )
		Rpc.ViewCache.exceptions = Settings.options.get('koo.cache_exceptions', [])

