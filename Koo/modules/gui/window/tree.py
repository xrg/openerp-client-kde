##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import gettext

from Common import api
from Common import common
from Common import options
from Common.viewsettings import *
import view_tree
import Rpc
import widget

from widget.model.treemodel import TreeModel

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

class tree( QWidget ): 
	def __init__( self, view, model, domain=[], context={}, name=False, parent=None ):
		QWidget.__init__(self,parent)
		loadUi( common.uiPath('tree.ui'), self ) 
		
		self.uiSplitter.setStretchFactor( 0, 0 )
		self.uiSplitter.setStretchFactor( 1, 2 )

		self.context=context
		self.model = view['model']
		if view.get('field_parent', False):
			self.domain = []
		else:
			self.domain = domain
		self.view = view

		# Next expression sounds absurd but field_parent contains the
		# name of the field that links to the children: 'child_id' for
		# the ir.ui.menu for example
		self.childrenField = self.view['field_parent']

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
		self.fields = Rpc.session.execute('/object', 'execute', self.model, 'fields_get', p.fieldsOrder + [self.childrenField])

		self.treeModel = TreeModel( self )
		self.treeModel.setFields( self.fields )
		self.treeModel.setFieldsOrder( p.fieldsOrder )
		self.treeModel.setIconForField( 'icon', 'name')
		self.treeModel.setChildrenForField( self.childrenField, p.fieldsOrder[0] )
		self.treeModel.setShowBackgroundColor( False )

		self.listModel = TreeModel( self )
		self.listModel.setMode( TreeModel.ListMode )
		self.listModel.setFields( self.fields )
		self.listModel.setFieldsOrder( p.fieldsOrder )
		self.listModel.setIconForField( 'icon', 'name' )
		self.listModel.setShowBackgroundColor( False )

		self.group = widget.model.group.ModelRecordGroup( self.model, self.fields, context = self.context )
		self.group.setDomain( domain )
		self.group.update()
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
		self.connect(self.uiShortcuts, SIGNAL('activated(QModelIndex)'), self.goToShortcut)
		self.connect(self.uiList.selectionModel(),SIGNAL('currentChanged(QModelIndex, QModelIndex)'),self.mainMenuClicked)

		if name:
			self.name = name
		else:
			self.name = p.title
		
		# Shortcuts

		scFields = Rpc.session.execute('/object', 'execute', 'ir.ui.view_sc', 'fields_get', ['res_id', 'name'])
		self.shortcutsGroup = widget.model.group.ModelRecordGroup( 'ir.ui.view_sc', scFields, context = self.context )
		self.shortcutsGroup.setDomain( [('user_id','=',Rpc.session.uid), ('resource','=',model)] )
		self.shortcutsGroup.update()

		self.shortcutsModel = TreeModel( self )
		self.shortcutsModel.setMode( TreeModel.ListMode )
		self.shortcutsModel.setFields( scFields )
		self.shortcutsModel.setFieldsOrder( ['name'] )
		self.shortcutsModel.setModelGroup( self.shortcutsGroup )
		self.shortcutsModel.setShowBackgroundColor( False )
		self.uiShortcuts.setModel( self.shortcutsModel )
		
		if not p.toolbar:
			self.uiList.hide()
		else:
			# Highlight the first element of the list and update the tree
			self.uiList.setCurrentIndex( self.uiList.moveCursor( QAbstractItemView.MoveHome, Qt.NoModifier ) )
			self.updateTree()
		self.restoreViewState()


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
		QApplication.setOverrideCursor( Qt.WaitCursor )
		self.group.update()
		self.uiList.setCurrentIndex( self.uiList.moveCursor( QAbstractItemView.MoveHome, Qt.NoModifier ) )
		self.updateTree()
		QApplication.restoreOverrideCursor()

	# TODO: Look if for some menu entries this has any sense. Otherwise
	# remove both functions. Of course we should connect the actions and
	# add them to the handlers dict if they are necessary.
	def printCurrent(self):
		self.executeAction(keyword='client_print_multi', report_type='html')

	def printHtmlCurrent(self):
		self.executeAction(keyword='client_print_multi')

	def executeAction(self, keyword='tree_but_action', id=None, report_type='pdf'):
		if id:
			api.instance.executeKeyword(keyword, {'model':self.model, 'id':id, 'report_type':report_type, 'ids': [id]})
		else:
			QMessageBox.information( self, '', _('No resource selected!'))

	def open(self, idx):
		id = self.treeModel.id( idx )
		if id:
			self.executeAction( 'tree_but_open', id )

	def editCurrentItem(self):
		id = self.treeModel.id( self.uiTree.currentIndex() )
		if id:
			api.instance.createWindow(None, self.model, id, self.domain)
		else:
			QMessageBox.information(self, '', _('No resource selected!'))

	def removeShortcut(self):
		id = self.currentShortcutId()
		if not id:
			return
		Rpc.session.execute('/object', 'execute', 'ir.ui.view_sc', 'unlink', [id])
		self.shortcutsGroup.update()

	def addShortcut(self):
		id = self.treeModel.id( self.uiTree.currentIndex() )
		if id == None:
			QMessageBox.information( self, _('No item selected'), _('Please select an element from the tree to add a shortcut to it.') )
			return
		res = Rpc.session.execute('/object', 'execute', self.model, 'name_get', [id], Rpc.session.context)
		for (id,name) in res:
			uid = Rpc.session.uid
			Rpc.session.execute('/object', 'execute', 'ir.ui.view_sc', 'create', {'resource':self.model, 'user_id':uid, 'res_id':id, 'name':name})
		self.shortcutsGroup.update()

	def goToShortcut(self, index):
		id = self.currentShortcutId()
		if not id:
			return
		m = self.shortcutsGroup[ id ]
		id = m.value( 'res_id' )
		self.executeAction('tree_but_open', id)

	def currentShortcutId(self):
		item = self.uiShortcuts.currentIndex()
		if not item.isValid():
			return None
		id = item.data( Qt.UserRole ).toInt()[0]
		return id

	# There's no reason why a menu can't be closed, is it?
	def canClose(self):
		self.storeViewState()
		return True
	
	def storeViewState(self):
		id = self.view['view_id']
		if not id:
			return
		header = self.uiTree.header()
		ViewSettings.store( id, str( header.saveState().toBase64() ) )
		
	def restoreViewState(self):
		id = self.view['view_id']
		if not id:
			return
		settings = ViewSettings.load( id )
		if not settings:
			return
		header = self.uiTree.header()
		header.restoreState( QByteArray.fromBase64( settings ) )
		
	def actions(self):
		return []

