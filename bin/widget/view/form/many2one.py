##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: many2one.py 4773 2006-12-05 11:01:20Z ced $
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

from common import api
from common import common

import widget
from widget.screen import Screen
from widget.model.group import ModelRecordGroup

from modules.gui.window.win_search import SearchDialog
import rpc

from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *


class ScreenDialog( QDialog ):
	def __init__(self, parent):
		QWidget.__init__( self, parent )
		loadUi( common.uiPath('dia_form_win_many2one.ui'), self )

		self.setMinimumWidth( 800 )
		self.setMinimumHeight( 600 )

		self.connect( self.pushOk, SIGNAL("clicked()"), self.accepted )
		self.connect( self.pushCancel, SIGNAL("clicked()"), self.reject )
		self.model = None
		self.screen = None

	def setup(self, model, id=None):
		if self.screen:
			return
		self.screen = Screen(self)
		self.screen.setModelGroup( ModelRecordGroup( model ) )
		self.screen.setViewTypes( ['form'] )
		if id:
			self.screen.load([id])
		else:
			self.screen.new()
		self.screen.display()
		self.layout().insertWidget( 0, self.screen  )
		self.screen.show()
		
	def setAttributes(self, attrs):
		if ('string' in attrs) and attrs['string']:
			self.setWindowTitle( self.windowTitle() + ' - ' + attrs['string'])

	def accepted( self ):
		self.screen.current_view.store()

		if self.screen.current_model.validate():
			self.accept()
			self.screen.save_current()
			self.model = self.screen.current_model.name()
			self.close()
		else:
			self.reject()

class ManyToOneFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		loadUi( common.uiPath('many2one.ui'), self )
		
		self.uiText.installEventFilter( self )
		self.connect( self.uiText, SIGNAL( "editingFinished()" ), self.match )
		self.connect( self.pushNew, SIGNAL( "clicked()" ), self.new )
		self.connect( self.pushOpen, SIGNAL( "clicked()" ), self.open )
		self.connect( self.pushClear, SIGNAL( "clicked()" ), self.clear )

 		self.modelType = attrs['relation']	
		# To build the menu entries we need to query the server so we only make 
		# the call if necessary and only once. Hence with self.menuLoaded we know
		# if we've got it in the 'cache'
 		self.menuLoaded = False
		self.newMenuEntries = []
 		self.newMenuEntries.append((_('Action'), lambda: self.executeAction('client_action_multi'), False))
 		self.newMenuEntries.append((_('Report'), lambda: self.executeAction('client_print_multi'), False))
 		self.newMenuEntries.append((None, None, None))

 		if attrs.get('completion',False):
 			ids = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', '', [], 'ilike', {})
 			if ids:
				self.loadCompletion( ids, attrs )

	def clear( self ):
		if self.model:
			self.model.setValue( self.name, False )
		self.uiText.clear()
		self.pushOpen.setIcon( QIcon( ":/images/images/find.png"))

	def eventFilter( self, target, event):
		if self.model and event.type() == QEvent.KeyPress :
			if event.key()==Qt.Key_F1:
				self.new()
				return True
			return False
		elif event.type() == QEvent.ContextMenu:
			self.showPopupMenu( target, event.globalPos() )
			return True
		return False

	def loadCompletion(self,ids,attrs):
		self.completion = QCompleter()
		self.completion.setCaseSensitivity( Qt.CaseInsensitive )
		self.uiText.setCompleter( self.completion )
		liststore = []
		for i,word in enumerate( ids ):
			if word[1][0] == '[':
				i = word[1].find( ']')
				s = word[1][1:i]
				s2 = word[1][i+2:]
				liststore.append( s2 )
			else:
				liststore.append( word[1] )
		self.completion.setModel( QStringListModel( liststore ) )
		self.completion.setCompletionColumn( 0 )

	def setReadOnly(self, value):
		self.uiText.setEnabled( not value )
		self.pushNew.setEnabled( not value )
		self.pushClear.setEnabled( not value )
		self.pushOpen.setEnabled( not value )

	def colorWidget(self):
		return self.uiText

	def match(self):
		name = unicode( self.uiText.text() )
		if name.strip() == '':
			return
		domain = self.model.domain( self.name )
		context = self.model.context()
		ids = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', name, domain, 'ilike', context)
		if len(ids)==1:
			self.model.setValue( self.name, ids[0] )
			self.display()
		else:
			dialog = SearchDialog(self.attrs['relation'], sel_multi=False, ids=[x[0] for x in ids], context=context, domain=domain)
			if dialog.exec_() == QDialog.Accepted and dialog.result:
				id = dialog.result[0]
				name = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_get', [id], rpc.session.context)[0]
				self.model.setValue(self.name, name)
				self.display()

	def open(self):
		if self.model.value(self.name):
			dialog = ScreenDialog( self )
			dialog.setAttributes( self.attrs )
			dialog.setup( self.attrs['relation'], self.model.get()[self.name] )
			if dialog.exec_() == QDialog.Accepted:
				self.model.setValue(self.name, dialog.model)
				self.display()
		else:
			domain = self.model.domain( self.name )
			context = self.model.context()
			dialog = SearchDialog(self.attrs['relation'], sel_multi=False, context=context, domain=domain)
			if dialog.exec_() == QDialog.Accepted and dialog.result:
				id = dialog.result[0]
				name = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_get', [id], rpc.session.context)[0]
				self.model.setValue(self.name, name)
				self.display()


	def new(self):
		dialog = ScreenDialog(self)
		dialog.setAttributes( self.attrs )
		dialog.setup( self.attrs['relation'] )
		if dialog.exec_() == QDialog.Accepted:
			self.model.setValue(self.name, dialog.model)
			self.display()

	def store(self):
		# No update of the model, the model is updated in real time 
		pass

	def reset(self):
		self.uiText.clear()
		
	def showValue(self):
		res = self.model.value(self.name)
 		if res:
			self.uiText.setText( res )
			self.pushOpen.setIcon( QIcon( ":/images/images/folder.png"))
			# pushOpen will always be enabled if it has to open an existing
			# element
			self.pushOpen.setEnabled( True )
 		else:
			self.uiText.clear()
 			self.pushOpen.setIcon( QIcon( ":/images/images/find.png"))
			# pushOpen won't be enabled if it is to find an element
			self.pushOpen.setEnabled( not self.isReadOnly() )
			

	def menuEntries(self):
		if not self.menuLoaded:
			fields_id = rpc.session.execute('/object', 'execute', 'ir.model.fields', 'search',[('relation','=',self.modelType),('ttype','=','many2one'),('relate','=',True)])
			fields = rpc.session.execute('/object', 'execute', 'ir.model.fields', 'read', fields_id, ['name','model_id'], rpc.session.context)
			models_id = [x['model_id'][0] for x in fields if x['model_id']]
			fields = dict(map(lambda x: (x['model_id'][0], x['name']), fields))
			models = rpc.session.execute('/object', 'execute', 'ir.model', 'read', models_id, ['name','model'], rpc.session.context)
			for model in models:
				field = fields[model['id']]
				model_name = model['model']
				f = lambda model_name,field: lambda: self.executeRelation(model_name,field)					
				self.newMenuEntries.append(('... '+model['name'], f(model_name,field), False))
			self.menuLoaded = True

		# Set enabled/disabled values
		value = self.model.value(self.name)
		if value:
			value = True
		else:
			value = False
		currentEntries = []
		for x in self.newMenuEntries:
			currentEntries.append( (x[0], x[1], value) )
		return currentEntries

	def executeRelation(self, model, field):
		# Open a view with ids: [(field,'=',value)]
		value = self.model.value(self.name)
		ids = rpc.session.execute('/object', 'execute', model, 'search',[(field,'=',value)])
		api.instance.createWindow(False, model, ids, [(field,'=',value)], 'form', None, mode='tree,form')
		return True

	def executeAction(self, type):
		id = self.model.id
		appi.instance.executeKeyword(type, {'model':self.modelType, 'id': id or False, 'ids':[id], 'report_type': 'pdf'})
		return True

