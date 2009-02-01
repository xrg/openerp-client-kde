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


import gettext
from Koo.Common import Api
from Koo.Common import Common


from Koo.Screen.Screen import Screen
from Koo.Model.Group import ModelRecordGroup

from Koo import Rpc
import time
from Koo.Dialogs.SearchDialog import SearchDialog
from Koo.Fields.AbstractFieldWidget import *

(ActionFieldWidgetUi, ActionFieldWidgetBase) = loadUiType( Common.uiPath('paned.ui') ) 

class ActionFieldWidget(AbstractFieldWidget, ActionFieldWidgetUi):
	def __init__(self,  parent, view, attrs={}):
		AbstractFieldWidget.__init__( self, parent, view, attrs )
		ActionFieldWidgetUi.__init__( self )
		self.setupUi( self )

		self.colors['normal'] = self.palette().color( self.backgroundRole() )	
		self.act_id=attrs['name']
		res = Rpc.session.execute('/object', 'execute', 'ir.actions.actions', 'read', [self.act_id], ['type'], Rpc.session.context)
		if not res:
			raise Exception, 'ActionNotFound'
		type=res[0]['type']

		
		self.action = Rpc.session.execute('/object', 'execute', type, 'read', [self.act_id], False, Rpc.session.context)[0]
		if 'view_mode' in attrs:
			self.action['view_mode'] = attrs['view_mode']

		if self.action['type']=='ir.actions.act_window':
			if not self.action.get('domain', False):
				self.action['domain']='[]'
			self.context = {'active_id': False, 'active_ids': []}
			self.context.update(eval(self.action.get('context', '{}'), self.context.copy()))
			a = self.context.copy()
			a['time'] = time
			self.domain = Rpc.session.evaluateExpression(self.action['domain'], a)

			if self.action['view_type']=='form':
				self.view_id = []
				if self.action['view_id']:
					self.view_id = [self.action['view_id'][0]]

				self.modelGroup = ModelRecordGroup( self.action['res_model'], context=self.context )
				self.modelGroup.setDomain( self.domain )

				# Try to make the impression that it loads faster...
				QTimer.singleShot( 0, self.createScreen )
			elif self.action['view_type']=='tree':
				pass #TODO
		self.screen = None

	def createScreen(self):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		self.modelGroup.update()
		self.screen = Screen( self )
		self.screen.setModelGroup( self.modelGroup )
		#self.screen.setDomain( self.domain )
		self.screen.setEmbedded( True )
		if int( self.attrs.get('show_toolbar','0') ):
			self.screen.setToolbarVisible( True )
		else:
			self.screen.setToolbarVisible( False )
		self.connect( self.screen, SIGNAL('activated()'), self.switch )
		mode = (self.action['view_mode'] or 'form,tree').split(',')
		#if self.view_id:
			#self.screen.setViewIds( self.view_id )
		#else:
			#self.screen.setViewTypes( mode )
		self.screen.setupViews( mode, self.view_id )
		self.uiTitle.setText( QString( self.attrs['string'] or "" ))
		layout = QVBoxLayout( self.uiGroup )
		layout.setContentsMargins( 0, 0, 0 , 0 )
		layout.addWidget( self.screen )

		self.connect( self.pushSearch, SIGNAL( 'clicked()' ), self.slotSearch )
		self.connect( self.pushSwitchView, SIGNAL( 'clicked()'), self.switch )
		self.connect( self.pushOpen, SIGNAL( 'clicked()' ), self.slotOpen )

		self.setSizePolicy( QSizePolicy.Expanding , QSizePolicy.Expanding )
		QApplication.restoreOverrideCursor()


	def sizeHint( self ):
		return QSize( 200, 400 )

	def switch( self ):
		self.screen.switchView()

	def slotSearch( self ):
		win = SearchDialog(self.action['res_model'], domain=self.domain, context=self.context)
		win.exec_()
 		if win.result:
 			self.screen.clear()
 			self.screen.load(win.result)

	def slotOpen( self ):
		Api.instance.execute(self.act_id )

	def store(self):
		self.screen.currentView().store()

	def showValue(self):
		self.modelGroup.update()
		if self.screen:
			self.screen.display()

