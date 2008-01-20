from PyQt4.QtCore import *
from PyQt4.QtGui import *
import rpc

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

	def load(self, fields, fieldsInfo = {}, fieldsInvertedInfo = {}):
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
			prefix.appendRow( node )

			# Fill in cache structures
			self.fieldsInvertedInfo[prefix_value+st_name] = prefix_node+field
			self.fieldsInfo[prefix_node+field] = fields[field]
			if prefix_node:
				self.fieldsInfo[prefix_node + field]['string'] = '%s%s' % (prefix_value, self.fieldsInfo[prefix_node + field]['string'])
			# If it's a relation look at the children
			if fields[field].get('relation', False) and level>0:
				fields2 = rpc.session.execute('/object', 'execute', fields[field]['relation'], 'fields_get', False, rpc.session.context)
				self.populate(fields2, prefix_node+field+'/', node, st_name+'/', level-1)


