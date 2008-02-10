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

import gettext

from common import common
import service
import view_tree
import rpc
import options
import widget

from widget.model.treemodel import TreeModel

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

class tree( QWidget ): 
	def __init__( self, view, model, res_id=False, domain=[], context={}, name=False, parent=None ):
		QWidget.__init__(self,parent)
		loadUi( common.uiPath('tree.ui'), self ) 
		
		self.context=context
		self.model = view['model']
		self.domain2 = domain
		if view.get('field_parent', False):
			self.domain = []
		else:
			self.domain = domain
		self.view = view

		# Next expression sounds absurd but field_parent contains the
		# name of the field that links to the children: 'child_id' for
		# the ir.ui.menu for example
		self.childrenField = self.view['field_parent']

		# Implement Reload properly. Should update model, toolbar and TreeView
		self.handlers = {
			'Switch': self.editCurrentItem,
			'Print': self.printCurrent,
			'PrintHtml': self.printHtmlCurrent,
			'Reload': self.reload,
		}

		p = view_tree.parser.TreeParser()
		p.parse( view['arch'] )
		self.toolbar = p.toolbar

		# Get all visible fields + parent field description
		self.fields = rpc.session.execute('/object', 'execute', self.model, 'fields_get', p.fieldsOrder + [self.childrenField])

		self.treeModel = TreeModel( self )
		self.treeModel.setFields( self.fields )
		self.treeModel.setFieldsOrder( p.fieldsOrder )
		self.treeModel.setIconForField( 'icon', 'name')
		self.treeModel.setChildrenForField( self.childrenField, 'name' )
		self.treeModel.setShowBackgroundColor( False )

		self.listModel = TreeModel( self )
		self.listModel.setFields( self.fields )
		self.listModel.setFieldsOrder( p.fieldsOrder )
		self.listModel.setIconForField( 'icon', 'name' )
		self.listModel.setChildrenForField( self.childrenField, 'name' )
		self.listModel.setShowBackgroundColor( False )

		self.group = widget.model.group.ModelRecordGroup( self.model, self.fields, context = self.context )
		self.loadGroup()
		if self.toolbar:
			self.listModel.setModelGroup( self.group )
		else:
			self.treeModel.setModelGroup( self.group )

		self.uiTree.setModel( self.treeModel )
		self.uiList.setModel( self.listModel )

		self.connect(self.uiTree,SIGNAL('activated( QModelIndex ) ' ), self.open )

		self.connect(self.pushAddShortcut, SIGNAL('clicked()'), self.addShortcut)
		self.connect(self.pushRemoveShortcut, SIGNAL('clicked()'), self.removeShortcut)
		self.connect(self.pushGoToShortcut, SIGNAL('clicked()'), self.goToShortcut)
		self.connect(self.uiShortcuts, SIGNAL('itemActivated(QTreeWidgetItem*,int)'), self.goToShortcut)
		self.connect(self.uiList.selectionModel(),SIGNAL('currentChanged(QModelIndex, QModelIndex)'),self.mainMenuClicked)

		if name:
			self.name = name
		else:
			self.name = p.title
		
		self.uiShortcuts.load( self.model )

		if not p.toolbar:
			self.uiList.hide()
		else:
			# Highlight the first element of the list and update the tree
			self.uiList.setCurrentIndex( self.uiList.moveCursor( QAbstractItemView.MoveHome, Qt.NoModifier ) )
			self.updateTree()


	def loadGroup(self):
		ids = rpc.session.execute('/object', 'execute', self.model, 'search', self.domain2)
		self.group.load( ids )

	def updateTree(self):
		item = self.uiList.currentIndex()
		if not item.isValid():
			return
		id = item.data( Qt.UserRole ).toInt()[0]
		if not id:
			return
		m = self.group[ id ]
		group = m.value( self.childrenField )
		group.addFields( self.group.fields )
		self.treeModel.setModelGroup( group )
		
	def mainMenuClicked( self, currentItem, previousItem ):
		self.updateTree()

	def reload(self):
		self.group.clear()
		self.loadGroup()
		self.uiList.setCurrentIndex( self.uiList.moveCursor( QAbstractItemView.MoveHome, Qt.NoModifier ) )
		self.updateTree()

	# TODO: Look if for some menu entries this has any sense. Otherwise
	# remove both functions. Of course we should connect the actions and
	# add them to the handlers dict if they are necessary.
	def printCurrent(self):
		self.executeAction(keyword='client_print_multi', report_type='html')

	def printHtmlCurrent(self):
		self.executeAction(keyword='client_print_multi')

	def executeAction(self, keyword='tree_but_action', id=None, report_type='pdf'):
		if id:
			obj = service.LocalService('action.main')
			obj.exec_keyword(keyword, {'model':self.model, 'id':id,
				'report_type':report_type})
		else:
			QMessageBox.information( self, '', _('No resource selected!'))

	def open(self, idx):
		id = self.treeModel.id( idx )
		if id:
			self.executeAction( 'tree_but_open', id )

	# TODO: improve with domain expr
	# TODO: Look at what it does, I don't find any action in the GTK client
	# for this...
	def sig_chroot(self):
		ids = self.ids()
		if len(ids) and self.domain:
			id = ids[0]
			datas = {'domain_field': self.domain[0][0], 'domain_value': id[0], 'res_id':id[0]}
			obj = service.LocalService('gui.window')
			obj.create(self.view, self.model, id[0], (self.domain[0],id[0]) )
		else:
			QMessageBox.information( self, '', _('Unable to chroot: no tree resource selected'))

	def editCurrentItem(self):
		id = self.treeModel.id( self.uiTree.currentIndex() )
		if id:
			obj = service.LocalService('gui.window')
			obj.create(None, self.model, id, self.domain)
		else:
			QMessageBox.information(self, '', _('No resource selected!'))

	def domain_id_get(self, tree=False):
		filter = []
		if self.domain and self.view.get('field_parent', False):
			filter = self.domain
		res = rpc.session.execute('/object', 'execute', self.model, 'search', filter)
		return res

	def removeShortcut(self):
		id = self.uiShortcuts.currentShortcutId()
		if id == None:
			return
		rpc.session.execute('/object', 'execute', 'ir.ui.view_sc', 'unlink', [id])
		self.uiShortcuts.load( self.model )

	def addShortcut(self):
		ids = self.uiTree.selectedIds()
		if ids == None:
			QMessageBox.information( self, _('No item selected'), _('Please select an element from the tree to add a shortcut to it.') )
			return
		res = rpc.session.execute('/object', 'execute', self.model, 'name_get', ids, rpc.session.context)
		for (id,name) in res:
			uid = rpc.session.uid
			rpc.session.execute('/object', 'execute', 'ir.ui.view_sc', 'create', {'resource':self.model, 'user_id':uid, 'res_id':id, 'name':name})
		self.uiShortcuts.load( self.model )

	def goToShortcut(self):
		id = self.uiShortcuts.currentMenuId()
		if id!=None:
			self.executeAction('tree_but_open', id)


	def id(self):
		try:
			return self.search[self.search_pos]
		except IndexError:
			return None

	# There's no reason why a menu can't be closed, is it?
	def canClose(self):
		return True
	
	def actions(self):
		return []
