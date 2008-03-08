##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: list.py 4411 2006-11-02 23:59:17Z pinky $
#      list.py Modified: 2007-03-31 11:00 Angel Alvarez  
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


class ViewTree( AbstractView ):

	def __init__(self, parent, fields):
		AbstractView.__init__(self, parent)
		self.treeModel = None
		self.view_type = 'tree'
		self.model_add_new = True
		self.reload = False
		self.title=""
		self.selecting = False

		self.widget = QTreeView( self )
		#self.widget.setSelectionMode( QAbstractItemView.SingleSelection )
		self.widget.setSortingEnabled(True)
		self.setAllowMultipleSelection(True)
		self.widget.setAlternatingRowColors( True )

		self.connect( self.widget, SIGNAL('activated(QModelIndex)'), self.activated )
		self.connect( self.widget, SIGNAL('doubleClicked(QModelIndex)'), self.activated )

		self.currentIndex = self.widget.rootIndex()

		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget( self.widget )
		self.setLayout( layout )
		self.setReadOnly( True )

	def setModel( self, model ):
		self.treeModel = model	
		self.widget.setModel( self.treeModel )
		self.connect( self.widget.selectionModel(),SIGNAL('currentChanged(QModelIndex, QModelIndex)'),self.currentChanged)

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
		self.emit( SIGNAL("currentChanged(int)"), self.treeModel.id(current) )

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
		self.widget.setSortingEnabled( value )
		if self._readOnly:
			self.widget.setEditTriggers( QAbstractItemView.NoEditTriggers ) 
		else:
			self.widget.setEditTriggers( QAbstractItemView.AllEditTriggers )

