##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

import rpc

from PyQt4.QtCore import *
from PyQt4.QtGui import *

## @brief The ShortcutsListWidget class handles a list of shortcuts, provided by 
# 'ir.ui.view_sc' model.
class ShortcutsListWidget(QTreeWidget):
	def __init__(self, parent):
		QTreeWidget.__init__(self, parent)
		self.setColumnCount(3)
		self.hideColumn( 0 )
		self.hideColumn( 2 )
		self.header().hide()

	## Loads the shortcuts stored for the given model 
	# @param model ie. 'ir.ui.menu'
	def load(self, model):
		uid =  rpc.session.uid
		sc = rpc.session.execute('/object', 'execute', 'ir.ui.view_sc', 'search', [('user_id','=',rpc.session.uid), ('resource','=',model)])
		self.clear()
		if len(sc):
			sc = rpc.session.execute('/object', 'execute', 'ir.ui.view_sc', 'read', sc, ['res_id', 'name'])
			for s in sc:
				item = QTreeWidgetItem()
				item.setText( 0, str(s['res_id']) )
				item.setText( 1, s['name'] )
				item.setText( 2, str(s['id']) )
				self.addTopLevelItem( item )

	## Returns the action id the shortcut is associated to
	def currentMenuId(self):
		item = self.currentItem()
		if item == None:
			return None
		return int(item.text(0))
	
	## Returns the shortcut id
	def currentShortcutId(self):
		item = self.currentItem()
		if item == None:
			return None
		return int(item.text(2))

