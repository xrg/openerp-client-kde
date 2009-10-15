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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Koo import Rpc

class FieldsModel( QStandardItemModel ):
	def __init__(self):
		QStandardItemModel.__init__(self)
		self.rootItem = self.invisibleRootItem()
		self.setColumnCount( 1 )
		self.setHeaderData( 0, Qt.Horizontal, QVariant( _('Fields') ) )

	def addField(self, text, data):
		item = QStandardItem( text )		
		item.setData( QVariant(data) )
		self.rootItem.appendRow( item )

	def load(self, fields, fieldsInfo = None, fieldsInvertedInfo = None):
		if fieldsInfo is None:
			fieldsInfo = {}
		if fieldsInvertedInfo is None:
			fieldsInvertedInfo = {}
		self.fieldsInfo = fieldsInfo
		self.fieldsInvertedInfo = fieldsInvertedInfo
		self.populate(fields)

	def populate(self, fields, prefix_node='', prefix=None, prefix_value='', level=2):
		fields_order = fields.keys()
		fields_order.sort(lambda x,y: -cmp(fields[x].get('string', ''), fields[y].get('string', '')))
		if prefix == None:
			prefix = self.rootItem
		for field in fields_order:
			st_name = fields[field]['string'] or field 
			node = QStandardItem(st_name) 
			node.setData( QVariant(field) )
			if fields[field].get('required', False):
				font = node.font()
				font.setBold( True )
				node.setFont( font )
			prefix.appendRow( node )

			# Fill in cache structures
			self.fieldsInvertedInfo[prefix_value+st_name] = prefix_node+field
			self.fieldsInfo[prefix_node+field] = fields[field]
			if prefix_node:
				self.fieldsInfo[prefix_node + field]['string'] = '%s%s' % (prefix_value, self.fieldsInfo[prefix_node + field]['string'])
			# If it's a relation look at the children
			if fields[field].get('relation', False) and level>0:
				fields2 = Rpc.session.execute('/object', 'execute', fields[field]['relation'], 'fields_get', False, Rpc.session.context)
				self.populate(fields2, prefix_node+field+'/', node, st_name+'/', level-1)
