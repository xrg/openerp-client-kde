##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: parser.py 4776 2006-12-05 13:21:09Z ced $
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

from widget.view.abstractparser import *

import time

from widget.view.form.many2one import dialog as M2ODialog
from modules.gui.window.win_search import win_search
from widget.model import treemodel

from tree import *
from PyQt4.uic import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from common import common
from common.numeric import *
from common.calendar import *



class TreeParser(AbstractParser):
	def create(self, parent, model, rootNode, fields, toolbar):
		self.screen = parent
		view = ViewTree( parent, fields )
		
		view.widget.setSortingEnabled(True)
		view.widget.setAlternatingRowColors( True )
		view.widget.setRootIsDecorated( False )

		attrs = common.node_attributes(rootNode)
 		on_write = attrs.get('on_write', '')
		view.setReadOnly( not attrs.get('editable', False) )

		if not view.title:
 			view.title = attrs.get('string', 'Unknown')

		colors = []
		for color_spec in attrs.get('colors', '').split(';'):
			if color_spec:
				colour, test = color_spec.split(':')
				colors.append( ( colour, str(test) ) )

		i=0
		header = []
		columns = []
		for node in rootNode.childNodes:
			node_attrs = common.node_attributes(node)
 			if node.localName == 'field':
				fname = node_attrs['name']
				twidth = {
					'integer': 60,
					'float': 80,
					'date': 70,
					'datetime': 120,
					'selection': 90,
					'char': 100,
					'one2many': 50,
				}

				if 'readonly' in node_attrs:
					fields[fname]['readonly'] = bool(int(node_attrs['readonly']))
				if 'required' in node_attrs:
					fields[fname]['required'] = bool(int(node_attrs['required']))

				node_attrs.update(fields[fname])

#				print "NODE_ATTRS: ", node_attrs
#				print "FIELDS: ", fields[fname]

				if 'width' in fields[fname]:
					width = int(fields[fname]['width'])
				else:
					width = twidth.get(fields[fname]['type'], 200)
				i = i +1
				header.append( { 'name': fname, 'type': fields[fname]['type'], 'string': fields[fname].get('string', '') })
				columns.append( { 'width': width , 'type': fields[fname]['type'], 'attributes':node_attrs } )

		model = treemodel.TreeModel( view )
		model.setMode( treemodel.TreeModel.ListMode )
		model.setModelGroup( self.screen.models )
		model.setFields( fields )
		model.setFieldsOrder( [x['name'] for x in header] )
		model.setColors( colors )
		if view.readOnly:
			model.setShowBackgroundColor( False )
		else:
			model.setShowBackgroundColor( True )
		view.setModel( model )

		for column in range( len(columns)):
			view.widget.setColumnWidth( column, columns[column]['width'] )
		 	if columns[column]['type'] == 'selection':
 				delegate = ComboBoxDelegate( columns[column]['attributes'], view.widget )
 				view.widget.setItemDelegateForColumn( column, delegate )
			elif columns[column]['type'] == 'int':
				delegate = IntegerDelegate( columns[column]['attributes'], view.widget )
				view.widget.setItemDelegateForColumn( column, delegate )
			elif columns[column]['type'] == 'float':
				delegate = FloatDelegate( columns[column]['attributes'], view.widget )
				view.widget.setItemDelegateForColumn( column, delegate )
			elif columns[column]['type'] == 'date':
				delegate = DateDelegate( columns[column]['attributes'], view.widget )
				view.widget.setItemDelegateForColumn( column, delegate )
			elif columns[column]['type'] == 'time':
				delegate = TimeDelegate( columns[column]['attributes'], view.widget )
				view.widget.setItemDelegateForColumn( column, delegate )
			elif columns[column]['type'] == 'datetime':
				delegate = DateTimeDelegate( columns[column]['attributes'], view.widget )
				view.widget.setItemDelegateForColumn( column, delegate )
		return view, on_write

class ComboBoxDelegate( QItemDelegate ):
	def __init__( self, attributes, parent=None):
		QItemDelegate.__init__( self, parent )
		self.list = attributes.get('selection', [])

	def createEditor( self, parent, option, index ):
		widget =  QComboBox( parent )
		i = 0
		current = -1
		for x in self.list:
			widget.addItem(x[1],QVariant(x[0]))
			if str(index.data( Qt.DisplayRole ).toString()) == x[1]:
				current = i
			i += 1
		return widget

	def setEditorData( self, editor, index ):
		if not editor:
			return
		idx = str(index.data(Qt.DisplayRole).toString())
		current = -1
		i = 0
		for x in self.list:
			if idx == x[1]:
				current = i
				break
			i += 1
		editor.setCurrentIndex( current )

	def setModelData( self, editor, model, index ):
		if editor:
			model.setData( index, QVariant(editor.currentText()), Qt.DisplayRole )
		
	def updateEditorGeometry(self, editor, option,index ):
		 editor.setGeometry(option.rect)

class StandardDelegate( QItemDelegate ):
	def __init__( self, attributes, parent=None):
		QItemDelegate.__init__( self, parent )

	def createEditor( self, parent, option, index ):
		return QLineEdit( parent )

	def updateEditorGeometry(self, editor, option,index ):
		 editor.setGeometry(option.rect)

class FloatDelegate( StandardDelegate ):
	def setEditorData( self, editor, index ):
		if not editor:
			return
		value, ok = index.data(Qt.DisplayRole).toDouble()
		editor.setText( str(value) )

	def setModelData( self, editor, model, index ):
		if editor:
			model.setData( index, QVariant(textToFloat(str(editor.text()))), Qt.DisplayRole )

class IntegerDelegate( StandardDelegate ):
	def setEditorData( self, editor, index ):
		if not editor:
			return
		value, ok = index.data(Qt.DisplayRole).toInt()
		editor.setText( str(value) )

	def setModelData( self, editor, model, index ):
		if editor:
			model.setData( index, QVariant(textToInteger(str(editor.text()))), Qt.DisplayRole )


class TimeDelegate( StandardDelegate ):
	def setEditorData( self, editor, index ):
		if not editor:
			return
		editor.setText( timeToText( index.data(Qt.DisplayRole).toTime() ) )

	def setModelData( self, editor, model, index ):
		if editor:
			model.setData( index, QVariant(textToTime(editor.text())), Qt.DisplayRole )

class CalendarWidget(QWidget):
	def __init__(self, showTime, parent):
		QWidget.__init__(self, parent)
		loadUi( common.uiPath('calendar.ui'), self)
		self.showTime = showTime
		self.connect( self.pushCalendar, SIGNAL('clicked()'), self.showCalendar )
		self.uiDate.setFocus()

	def showCalendar(self):
		PopupCalendar( self.uiDate, self.showTime)

class DateDelegate( StandardDelegate ):
	def createEditor( self, parent, option, index ):
		return CalendarWidget( showTime = False, parent = parent )

	def setEditorData( self, editor, index ):
		if not editor:
			return
		editor.uiDate.setText( dateToText( index.data(Qt.DisplayRole).toDate() ) )

	def setModelData( self, editor, model, index ):
		if editor:
			model.setData( index, QVariant(textToDate(editor.uiDate.text())), Qt.DisplayRole )

class DateTimeDelegate( StandardDelegate ):
	def createEditor( self, parent, option, index ):
		return CalendarWidget( showTime = True, parent = parent )

	def setEditorData( self, editor, index ):
		if not editor:
			return
		editor.uiDate.setText( dateTimeToText( index.data(Qt.DisplayRole).toDateTime() ) )

	def setModelData( self, editor, model, index ):
		if editor:
			model.setData( index, QVariant(textToDateTime(editor.uiDate.text())), Qt.DisplayRole )
# vim:noexpandtab:
