##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
# Copyright (c) 2007 Angel Alvarez <angel@nan-tic.com>
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

from widget.model import treemodel
from widget.view.abstractview import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from common import numeric
import rpc

class TinyTreeView(QTreeView):
	
	def moveCursor(	self, action, modifiers ):
		index = self.currentIndex()
		if not index.isValid():
			return QModelIndex()
		row = index.row()
		column = index.column()
		lastRow = index.model().rowCount() - 1
		lastColumn = index.model().columnCount() - 1
		if action == QAbstractItemView.MoveUp:
			row -= 1
		elif action == QAbstractItemView.MoveDown:
			row += 1
		elif action == QAbstractItemView.MoveLeft:
			column -= 1
		elif action == QAbstractItemView.MoveRight:
			column += 1
		elif action == QAbstractItemView.MoveHome:
			if column == 0:
				row = 0
			else:
				column = 0 
		elif action == QAbstractItemView.MoveEnd:
			if column == lastColumn:
				row = lastRow
			else:
				column = lastColumn
		elif action == QAbstractItemView.MovePageUp:
			row -= 12 
		elif action == QAbstractItemView.MovePageDown:
			row += 12 
		elif action == QAbstractItemView.MoveNext:
			column += 1
		elif action == QAbstractItemView.MovePrevious:
			column -= 1

		if column > lastColumn:
			column = 0
			row += 1
		elif column < 0:
			column = lastColumn
			row -= 1
		if row < 0:
			column = 0
			row = 0
		elif row > lastRow:
			row = lastRow
			column = 0
		return self.model().createIndex( row, column, index.internalPointer() ) 

class ViewTree( AbstractView ):

	def __init__(self, parent, fields):
		AbstractView.__init__(self, parent)
		self.treeModel = None
		self.view_type = 'tree'
		self.model_add_new = True
		self.reload = False
		self.title=""
		self.selecting = False

		#self.widget = QTableView( self )
		#self.widget.setSortingEnabled( True )
		#self.widget.setShowGrid( False )


		#self.widget = QTreeView( self )
		self.widget = TinyTreeView( self )
		self.widget.setAllColumnsShowFocus( False )
		self.widget.setSortingEnabled(True)
		self.widget.setRootIsDecorated( False )
		self.widget.setAlternatingRowColors( True )
		#self.widget.verticalScrollBar().setTracking( False )
		self.widget.setVerticalScrollMode( QAbstractItemView.ScrollPerItem )
		self.widget.sortByColumn( 0, Qt.AscendingOrder )

		# Contains list of aggregated fields
		self.aggregates = []
		self.aggregatesContainer = QWidget( self )
		self.aggregatesLayout = QHBoxLayout( self.aggregatesContainer )
		self.aggregatesLayout.setContentsMargins( 0, 0, 0, 0 )

		# We set uniformRowHeights property to True because this allows some 
		# optimizations. It makes a really big difference in models with thousands 
		# of tuples because moving to the end of the list only requires to query
		# for those items at the end (those that are shown) wheras if we don't
		# guarantee that all items have the same height, all previous items
		# need to be loaded too so the view can measure what height they are
		# and in which position the scroll is.
		self.widget.setUniformRowHeights( True )

		self.setAllowMultipleSelection(True)

		self.connect( self.widget, SIGNAL('activated(QModelIndex)'), self.activated )

		self.currentIndex = self.widget.rootIndex()

		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget( self.widget )
		layout.addWidget( self.aggregatesContainer )
		self.setLayout( layout )
		self.setReadOnly( True )


	def setModel( self, model ):
		self.treeModel = model	
		self.widget.setModel( self.treeModel )
		self.connect( self.widget.selectionModel(),SIGNAL('currentChanged(QModelIndex, QModelIndex)'),self.currentChanged)
		self.connect( self.treeModel, SIGNAL('rowsInserted(const QModelIndex &,int,int)'), self.updateAggregates )
		self.connect( self.treeModel, SIGNAL('rowsRemoved(const QModelIndex &,int,int)'), self.updateAggregates )
		self.connect( self.treeModel, SIGNAL('modelReset()'), self.updateAggregates )


	def addAggregate( self, name, label, bold, digits ):
		aggLabel = QLabel( label + ':', self.aggregatesContainer )
		aggLabel.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
		aggValue = QLabel( self.aggregatesContainer )
		aggValue.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
		if bold:
			font = QFont()
			font.setBold( True )
			aggLabel.setFont( font )
			aggValue.setFont( font )
		self.aggregatesLayout.addWidget( aggLabel )
		self.aggregatesLayout.addWidget( aggValue )
		self.aggregatesLayout.addSpacing( 10 )
		self.aggregates.append( { 'name': name, 'widget': aggValue, 'digits': digits } )

	def finishAggregates(self):
		self.aggregatesLayout.addStretch( 0 )

	# This signal is emited when a list item is double clicked
	# or activated, only when it's read-only.
	# Used by the search dialog to "accept" the choice or by
	# Screen to switch view
	def activated(self, index):
		if self._readOnly:
			self.emit( SIGNAL('activated()') )

	def __getitem__(self, name):
		return None

	def currentChanged(self, current):
		if self.selecting:
			return
		self.currentIndex = current
		# We send the current model. Previously we sended only the id of the model, but
		# new models have id=None
		self.emit( SIGNAL("currentChanged(PyQt_PyObject)"), self.treeModel.modelFromIndex(current) )
		self.updateAggregates()

	def store(self):
		pass

	def reset(self):
		pass

	def setSelected(self, model):
		return
		idx = self.treeModel.indexFromId(model)
		if idx != None:
			self.selecting = True
			self.widget.selectionModel().setCurrentIndex( idx, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
			self.selecting = False

	def display(self, currentModel, models):
		# TODO: Avoid setting the model group each time...
		self.treeModel.setModelGroup( models )
		#self.widget.header().resizeSections( QHeaderView.ResizeToContents )
		self.updateAggregates()
		if not currentModel:
			return
			item = self.treeModel.item(0)
			if not item:
				return
			idx = self.treeModel.indexFromItem(item)
			
			self.widget.setCurrentIndex( idx )
			self.widget.selectionModel().select( self.widget.currentIndex(), QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows )
		else:
			idx = self.treeModel.indexFromId( currentModel.id )
			if idx:
				self.widget.setCurrentIndex( idx )
				self.widget.selectionModel().select( self.widget.currentIndex(), QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows )

	def selectedIds(self):
		ids = []
		selectedIndexes = self.widget.selectionModel().selectedRows()
		for i in selectedIndexes:
			ids.append( self.treeModel.id( i ) )
		return ids

	def setAllowMultipleSelection(self, value):
		if value:
			self.widget.setSelectionMode( QAbstractItemView.ExtendedSelection )
		else:
			self.widget.setSelectionMode( QAbstractItemView.SingleSelection )

	def setReadOnly(self, value):
		self._readOnly = value
		# We only allow changing sort order when the view is read only
		# TODO: Uncomment this
		#self.widget.setSortingEnabled( value )
		if self._readOnly:
			self.widget.setEditTriggers( QAbstractItemView.NoEditTriggers ) 
		else:
			#self.widget.setEditTriggers( QAbstractItemView.AllEditTriggers )
			self.widget.setEditTriggers( QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed )
	
	def isReadOnly(self):
		return self._readOnly

	def updateAggregates(self):
		for agg in self.aggregates:
			value = 0.0
			for model in self.treeModel.group:
				value += model.value(agg['name'])
			agg['widget'].setText( numeric.floatToText( value, agg['digits'] ) )

	def viewSettings(self):
		header = self.widget.header()
		return str( header.saveState().toBase64() )

	def setViewSettings(self, settings):
		if not settings:
			return
		header = self.widget.header()
		header.restoreState( QByteArray.fromBase64( settings ) )

