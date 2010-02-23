##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

from PyQt4.QtGui import *
from Koo.Common import Common
import Koo.Common.Plugins
import re
import os

class Plugins:
	plugins = {}

	## @brief This function obtains the list of all available plugins by iterating
	# over every subdirectory inside Plugins/
	# 
	# This means that some plugins are activated the first time this function is 
	# called.
	@staticmethod
	def list( model = None ):
		# Search for all available plugins
		# Scan only once
		if not Plugins.plugins:
			Koo.Common.Plugins.scan( 'Koo.Plugins', os.path.abspath(os.path.dirname(__file__)) )

		plugins = {}
		for name, plugin in Plugins.plugins.items():
			if model:
				if plugin['model_regexp'].search( model ):
					plugins[name] = plugin
			else:
				plugins[name] = plugin
		return plugins

	## @brief Executes the given plugin.
	@staticmethod
	def execute(plugin, model, id, ids, context):
		plugins = Plugins.list()
		action = plugins[plugin]['action']
		action( model, id, ids, context )

	@staticmethod
	def register(name, model, title, action):
		Plugins.plugins[ name ] = {
			'model': model,
			'string': title,
			'action': action,
			'model_regexp': re.compile( model )
		}
