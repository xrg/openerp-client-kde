##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from Koo.View.AbstractParser import *

import time

from Koo.Model import KooModel

from TreeView import *
from PyQt4.uic import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo.FieldWidgets.FieldWidgetFactory import *
from Koo.Common import Common
from Koo.Common.Numeric import *
from Koo.Common.Calendar import *



class TreeParser(AbstractParser):
	def create(self, parent, model, rootNode, fields):
		self.screen = parent
		view = TreeView( parent, fields )
		
		attrs = Common.nodeAttributes(rootNode)
 		on_write = attrs.get('on_write', '')

		if not view.title:
 			view.title = attrs.get('string', 'Unknown')

		colors = []
		for color_spec in attrs.get('colors', '').split(';'):
			if color_spec:
				colour, test = color_spec.split(':')
				colors.append( ( colour, str(test) ) )

		header = []
		columns = []
		for node in rootNode.childNodes:
			node_attrs = Common.nodeAttributes(node)
 			if node.localName == 'field':
				fname = node_attrs['name']
				twidth = {
					'integer': 60,
					'float': 80,
					'date': 70,
					'datetime': 130,
					'selection': 130,
					'char': 140,
					'one2many': 50,
				}

				if 'readonly' in node_attrs:
					fields[fname]['readonly'] = bool(int(node_attrs['readonly']))
				if 'required' in node_attrs:
					fields[fname]['required'] = bool(int(node_attrs['required']))

				if 'sum' in node_attrs and fields[fname]['type'] in ('integer', 'float', 'float_time'):
					bold = bool(int(node_attrs.get('sum_bold', 0)))
					label = node_attrs['sum']
					digits = fields.get('digits', (16,2))
					view.addAggregate( fname, label, bold, digits ) 

				node_attrs.update(fields[fname])

				if 'width' in fields[fname]:
					width = int(fields[fname]['width'])
				else:
					width = twidth.get(fields[fname]['type'], 200)
				header.append( { 'name': fname, 'type': fields[fname]['type'], 'string': fields[fname].get('string', '') })
				columns.append( { 'width': width , 'type': fields[fname]['type'], 'attributes':node_attrs } )

		view.finishAggregates()

		model = KooModel.KooModel( view )
		model.setMode( KooModel.KooModel.ListMode )
		model.setModelGroup( self.screen.models )
		model.setFields( fields )
		model.setFieldsOrder( [x['name'] for x in header] )
		model.setColors( colors )
		model.setReadOnly( not attrs.get('editable', False) )
		view.setReadOnly( not attrs.get('editable', False) )

		if view.isReadOnly():
			model.setShowBackgroundColor( False )
		else:
			model.setShowBackgroundColor( True )
		view.setModel( model )

		for column in range( len(columns)):
			current = columns[column]
			view.widget.setColumnWidth( column, current['width'] )

			if not model.readOnly():
				# Assign delegates to editable models only. Editable delegates need
				# somewhat heigher rows (StandardDelegate.sizeHint()) which read only
				# models don't need. This way we save some space in read only views.
				delegate = StandardDelegate( current['type'], current['attributes'], view.widget )
				view.widget.setItemDelegateForColumn( column, delegate )
		return view, on_write

#from Koo.View.Form import calendar
#from Koo.View.Form import float
#from Koo.View.Form import integer
#from Koo.View.Form import char
#from Koo.View.Form import checkbox
#from Koo.View.Form import reference
#from Koo.View.Form import binary
#from Koo.View.Form import textbox
#from Koo.View.Form import richtext
#from Koo.View.Form import many2many
#from Koo.View.Form import many2one
#from Koo.View.Form import selection
#from Koo.View.Form import one2many
#from Koo.View.Form import url
#from Koo.View.Form import image


#widgetsType = {
#	'date': calendar.DateFormWidget,
#	'time': calendar.TimeFormWidget,
#	'datetime': calendar.DateTimeFormWidget,
#	'float': float.FloatFormWidget,
#	'integer': integer.IntegerFormWidget,
#	'selection': selection.SelectionFormWidget,
#	'char': char.CharFormWidget,
#	'boolean': checkbox.CheckBoxFormWidget,
#	'reference': reference.ReferenceFormWidget,
#	'binary': binary.BinaryFormWidget,
#	'text': char.CharFormWidget,
#	'text_tag': char.CharFormWidget,
#	#'one2many': one2many.OneToManyFormWidget,
#	#'one2many_form': one2many.OneToManyFormWidget,
#	#'one2many_list': one2many.OneToManyFormWidget,
#	#'many2many': many2many.ManyToManyFormWidget,
#	'many2one': many2one.ManyToOneFormWidget,
#	'image' : image.ImageFormWidget,
#	'url' : url.UrlFormWidget,
#	'email' : url.EMailFormWidget,
#	'callto' : url.CallToFormWidget,
#	'sip' : url.SipFormWidget,
#}

class StandardDelegate( QItemDelegate ):
	def __init__( self, type, attributes, parent=None):
		QItemDelegate.__init__( self, parent )
		self.attributes = attributes
		self.type = type
		self.currentIndex = None
		self.currentEditor = None

		# We pick QComboBox sizeHint height as the minimum
		# row height. This way editable views will have enough
		# room so widgets won't be clipped.
		combo = QComboBox()
		self.minimumHeight = combo.sizeHint().height()
		del combo

	def createEditor( self, parent, option, index ):
		self.currentIndex = index.model().createIndex( index.row(), index.column(), index.internalPointer() )
		if self.type in ('one2many', 'one2many_list', 'one2many_form', 'many2many'):
			return None
		widget = FieldWidgetFactory.create( self.type, parent, None, self.attributes )
		for x in widget.findChildren(QWidget):
			w = x.nextInFocusChain()
			inside = False
			while w:
				if w == widget:
					inside = True
					break
				w = w.parent()
			if not inside:
				x.installEventFilter( self )
				break
		self.currentEditor = widget
		index.model()._updatesEnabled = False
		return widget

	def eventFilter( self, obj, event ):
		if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
			self.emit(SIGNAL('commitData(QWidget*)'), self.currentEditor)
			self.emit(SIGNAL('closeEditor(QWidget*, QAbstractItemDelegate::EndEditHint)'), self.currentEditor, QAbstractItemDelegate.NoHint)

			parent = self.parent()
			if parent.inherits( 'QAbstractItemView' ):
				model = self.currentIndex.model()
				row = self.currentIndex.row()

				# Check whether we have to move to the next item or the
				# previous one
				if event.modifiers() and Qt.ShiftModifier:
					# Previous item
					column = self.currentIndex.column() - 1
					if column < 0:
						column = model.columnCount( self.currentIndex.parent() ) - 1
						row = self.currentIndex.row() - 1
						if row < 0:
							row = model.rowCount( self.currentIndex.parent() ) - 1
				else:
					# Next item
					column = self.currentIndex.column() + 1
					if column >= model.columnCount( self.currentIndex.parent() ):
						column = 0
						row = self.currentIndex.row() + 1
						if row >= model.rowCount( self.currentIndex.parent() ):
							row = 0
				index = model.createIndex( row, column, self.currentIndex.internalPointer() )
				# Set current index per Qt4 documentation before trying to edit
				parent.setCurrentIndex( index )
				parent.edit( index )
			return True
		return QItemDelegate.eventFilter( self, obj, event )

	def setEditorData( self, editor, index ):
		if not editor:
			return
		# We assume a KooModel here
		model = index.model().modelFromIndex( index )
		editor.load( model )
		return

	def setModelData( self, editor, model, index ):
		model._updatesEnabled = True
		#if editor:
			#editor.store()
		
	def updateEditorGeometry(self, editor, option, index ):
		 editor.setGeometry(option.rect)
	
	# As noted above height will be the maximum between standard Delegate
	# and QComboBox sizeHint height. Which should usually result in
	# QComboBox measure. This ensures widgets fit correctly.
	def sizeHint(self, option, index ):
		size = QItemDelegate.sizeHint( self, option, index )
		size.setHeight( max(size.height(), self.minimumHeight ) )
		return size

# vim:noexpandtab:
