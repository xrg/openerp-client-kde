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
		'language': False,
		'path.share': os.path.join(sys.prefix, 'share/Koo/'),
		'path.pixmaps': os.path.join(sys.prefix, 'share/pixmaps/Koo/'),
		'path.ui': os.path.join(sys.prefix, 'share/Koo/ui'), 
		'tip.autostart': False,
		'tip.position': 0,
		'print_directly': False,
		'client.default_path': os.path.expanduser('~'),
		'stylesheet' : '',
		'tabs_position' : 'top',
		'tabs_closable' : True,
		'show_toolbar' : True,
		'sort_mode' : 'all_items',
		'pos_mode' : False,
		'kde.enabled' : True,
		'attachments_dialog' : False,
	}

	## @brief Stores current settings in the appropiate config file.
	@staticmethod
	def saveToFile():
		if not Settings.rcFile:
			Debug.warning( 'No rc file specified.' )
			return False
		try:
			p = ConfigParser.ConfigParser()
			sections = {}
			for o in Settings.options.keys():
				if not len(o.split('.'))==2:
					continue
				osection,oname = o.split('.')
				if not p.has_section(osection):
					p.add_section(osection)
				p.set(osection,oname,Settings.options[o])
			p.write(file(Settings.rcFile,'wb'))
		except:
			Debug.warning( 'Unable to write config file %s !' % Settings.rcFile )
		return True

	## @brief Loads settings from the appropiate config file.
	@staticmethod
	def loadFromFile():
		if not Settings.rcFile:
			Debug.warning( 'No rc file specified.' )
			return False
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

	## @brief Sets the value for the given key.
	@staticmethod
	def setValue(key, value):
		Settings.options[key]=value

	## @brief Returns the value for the given key.
	@staticmethod
	def value(key, defaultValue=None):
		return Settings.options.get(key, defaultValue)

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
		Settings.options.update( settings )
		Rpc.ViewCache.exceptions = Settings.options.get('cache_exceptions', [])

