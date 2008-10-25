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
from Common import common
import re
import os

class Plugins:
	## @brief This function obtains the list of all available plugins by iterating
	# over every subdirectory inside Plugins/
	@staticmethod
	def list():
		# Search for all available plugins
		plugs = {}
		dir=os.path.abspath(os.path.dirname(__file__))
		for i in os.listdir(dir):
			path = os.path.join( dir, i, '__terp__.py' )
			if os.path.isfile( path ):
				try:
					x = eval(file(path).read())
					# Store the module we need to import in order
					# to execute the 'action'
					for y in x:
						x[y]['module'] = i
					plugs.update( x )
				except:
					print "Error importing view: ", i
		return plugs
		

	##@brief Shows the plugin selection dialog and executes the one selected
	@staticmethod
	def showDialog(datas):
		result = {}
		plugins = Plugins.list()
		for p in plugins:
			if not 'model_re' in plugins[p]:
				plugins[p]['model_re'] = re.compile(plugins[p]['model'])
			res = plugins[p]['model_re'].search(datas['model'])
			if res:
				result[plugins[p]['string']] = p
		if not len(result):
			QMessageBox.information(None, '',_('No available plugin for this resource !'))
			return 
		sel = common.selection(_('Choose a Plugin'), result, alwaysask=True)
		if sel:
			# Import the appropiate module and execute the action
			exec('import %s' % plugins[sel[1]]['module'])
			exec('%s(%s)' % ( plugins[sel[1]]['action'], datas ) )
	@staticmethod
	def execute(plugin, model, id, ids):
		plugins = Plugins.list()
		datas = { 'model': model, 'id': id, 'ids': ids }
		exec('import %s' % plugins[plugin]['module'])
		exec('%s(%s)' % ( plugins[plugin]['action'], datas ) )

