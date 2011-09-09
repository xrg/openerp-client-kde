##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#					Fabien Pinckaers <fp@tiny.Be>
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
from Koo.Common import Common
from Koo.Common.Settings import *

from Koo import Rpc

from Koo.Screen import Screen
from Koo.Screen.ScreenDialog import ScreenDialog
from Koo.Model.Group import RecordGroup

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from Common.Ui import *

(SearchDialogUi, SearchDialogBase) = loadUiType( Common.uiPath('win_search.ui') )

class SearchDialog( QDialog, SearchDialogUi ):
	def __init__(self, model, sel_multi=True, ids=None, context=None, domain = None, parent = None):
		QDialog.__init__( self, parent )
		SearchDialogUi.__init__( self )
		self.setupUi( self )

		if ids is None:
			ids = []
		if context is None:
			context = {}
		if domain is None:
			domain = []

		self.setModal( True )

		self.ids = ids
		self.result = None
		self.context = context
		self.context.update(Rpc.session.context)
		self.allowMultipleSelection = sel_multi

		self.modelGroup = RecordGroup( model, context=self.context )
		if Settings.value('koo.sort_mode') == 'visible_items':
			self.modelGroup.setSortMode( RecordGroup.SortVisibleItems )
		self.modelGroup.setDomain( domain )
		if self.ids:
			self.modelGroup.setFilter( [('id','in',ids)] )
			#self.reload()

		self.screen.setRecordGroup( self.modelGroup )
		self.screen.setViewTypes( ['tree'] )

		self.view = self.screen.currentView()
		self.view.setAllowMultipleSelection( self.allowMultipleSelection )
		self.view.setReadOnly( True )
		self.connect( self.view, SIGNAL('activated()'), self.accepted )

		self.model = model

		view_form = Rpc.session.execute('/object', 'execute', self.model, 'fields_view_get', False, 'form', self.context)
		self.form.setup( view_form['arch'], view_form['fields'], model, domain )
		self.form.hideButtons()
		self.connect( self.form, SIGNAL('keyDownPressed()'), self.setFocusToList )

		self.title = _('Search: %s') % self.form.name
		self.titleResults = _('Search: %s (%%d result(s))') % self.form.name

		self.setWindowTitle( self.title )


		# TODO: Use Designer Widget Promotion instead
		layout = self.layout()
		layout.insertWidget(0, self.screen )
		layout.insertWidget(0, self.form )

		self.form.setFocus()

		self.connect( self.pushNew, SIGNAL( "clicked()"), self.new )
		self.connect( self.pushAccept, SIGNAL( "clicked()"), self.accepted )
		self.connect( self.pushCancel , SIGNAL( "clicked()"), self.reject )
		self.connect( self.pushFind, SIGNAL( "clicked()"), self.find )
		self.connect( self.form, SIGNAL( "search()" ), self.find )

		# Selects all items
		self.select()

	def setFocusToList(self):
		self.screen.setFocus()

	def find(self):
		self.modelGroup.setFilter( self.form.value() )
		self.reload()

	def reload(self):
		self.modelGroup.update()
		self.select()

	def select(self):
		if self.allowMultipleSelection:
			self.view.selectAll()
		self.setWindowTitle( self.titleResults % self.modelGroup.count() )

	def accepted( self ):
		self.result = self.screen.selectedIds() or self.ids
		self.accept()

	def new(self):
		self.hide()
		dialog = ScreenDialog( self )
		dialog.setContext( self.context )
		dialog.setDomain( self.modelGroup.domain() )
		dialog.setup( self.model )
		if dialog.exec_() == QDialog.Accepted:
			self.result = [dialog.recordId]
			self.accept()
		else:
			self.reject()

# vim:noexpandtab:
