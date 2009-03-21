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
from Koo.Common import Shortcuts

from Koo.Screen.Screen import Screen
from Koo.Model.Group import ModelRecordGroup

from Koo.Dialogs.SearchDialog import SearchDialog
from Koo import Rpc

from Koo.Fields.AbstractFieldWidget import *
from Koo.Fields.AbstractFieldDelegate import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

(ScreenDialogUi, ScreenDialogBase) = loadUiType( Common.uiPath('dia_form_win_many2one.ui') ) 

class ScreenDialog( QDialog, ScreenDialogUi ):
	def __init__(self, parent):
		QWidget.__init__( self, parent )
		ScreenDialogUi.__init__( self )
		self.setupUi( self )

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
		self.screen.currentView().store()

		if self.screen.currentRecord().validate():
			self.accept()
			self.screen.save()
			self.model = self.screen.currentRecord().name()
			self.close()
		else:
			self.reject()

(ManyToOneFieldWidgetUi, ManyToOneFieldWidgetBase ) = loadUiType( Common.uiPath('many2one.ui') ) 

class ManyToOneFieldWidget(AbstractFieldWidget, ManyToOneFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		ManyToOneFieldWidgetUi.__init__(self)
		self.setupUi(self)
		
		self.uiText.installEventFilter( self )
		self.connect( self.uiText, SIGNAL( "editingFinished()" ), self.match )
		self.connect( self.pushNew, SIGNAL( "clicked()" ), self.new )
		self.connect( self.pushOpen, SIGNAL( "clicked()" ), self.open )
		self.connect( self.pushClear, SIGNAL( "clicked()" ), self.clear )

		# Create shortcuts
		self.scNew = QShortcut( self.uiText )
		self.scNew.setKey( Shortcuts.CreateInField )
		self.scNew.setContext( Qt.WidgetShortcut )
		self.connect( self.scNew, SIGNAL('activated()'), self.new )

		self.scSearch = QShortcut( self.uiText )
		self.scSearch.setKey( Shortcuts.SearchInField )
		self.scSearch.setContext( Qt.WidgetShortcut )
		self.connect( self.scSearch, SIGNAL('activated()'), self.open )

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
 			ids = Rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', '', [], 'ilike', {})
 			if ids:
				self.loadCompletion( ids, attrs )

	def clear( self ):
		# As the 'clear' button might modify the model we need to be sure all other fields/widgets
		# have been stored in the model. Otherwise the recordChanged() triggered by modifying
		# the parent model could make us lose changes.
		self.view.store()

		if self.model:
			self.model.setValue( self.name, False )
		self.uiText.clear()
		self.pushOpen.setIcon( QIcon( ":/images/images/find.png"))

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
			self.model.setValue( self.name, False )			
			self.showValue()
			return
		if name == self.model.value(self.name):
			return
		self.search( name )

	def open(self):
		# As the 'open' button might modify the model we need to be sure all other fields/widgets
		# have been stored in the model. Otherwise the recordChanged() triggered by modifying
		# the parent model could make us lose changes.
		self.view.store()

		if self.model.value(self.name):
			# If Control Key is pressed when the open button is clicked
			# the record will be opened in a new tab. Otherwise it's opened
			# in a new modal dialog.
			if QApplication.keyboardModifiers() & Qt.ControlModifier:
				model = self.attrs['relation']
				id = self.model.get()[self.name]
				Api.instance.createWindow(False, model, id, [], 'form', mode='form,tree')
			else:	
				dialog = ScreenDialog( self )
				dialog.setAttributes( self.attrs )
				dialog.setup( self.attrs['relation'], self.model.get()[self.name] )
				if dialog.exec_() == QDialog.Accepted:
					self.model.setValue(self.name, dialog.model)
					self.display()
		else:
			self.search('')

	# This function searches the given name within the available records. If none or more than
	# one possible name matches the search dialog is shown. If only one matches we set the
	# value and don't even show the search dialog. This is also true if the function is called
	# with "name=''" and only one record exists in the database (hence the call from open())
	def search(self, name):
		domain = self.model.domain( self.name )
		context = self.model.context()
		ids = Rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', name, domain, 'ilike', context)
		if ids and len(ids)==1:
			self.model.setValue( self.name, ids[0] )
			self.display()
		else:
			dialog = SearchDialog(self.attrs['relation'], sel_multi=False, ids=[x[0] for x in ids], context=context, domain=domain)
			if dialog.exec_() == QDialog.Accepted and dialog.result:
				id = dialog.result[0]
				name = Rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_get', [id], Rpc.session.context)[0]
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
			related = Rpc.session.execute('/object', 'execute', 'ir.values', 'get', 'action', 'client_action_relate', [(self.modelType, False)], False, Rpc.session.context)
			actions = [x[2] for x in related]
			for action in actions:
				f = lambda action: lambda: self.executeRelation(action)
				self.newMenuEntries.append(('... '+ action['name'], f(action), False))
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

	def executeRelation(self, action):
		id = self.model.get()[self.name]
		group = ModelRecordGroup( self.attrs['relation'] )
		group.load( [id] )
		record = group.modelByIndex( 0 )
		action['domain'] = record.evaluateExpression( action['domain'], check_load=False)
		action['context'] = str( record.evaluateExpression( action['context'], check_load=False) )
		Api.instance.executeAction( action )

	def executeAction(self, type):
		id = self.model.id
		Api.instance.executeKeyword(type, {'model':self.modelType, 'id': id or False, 'ids':[id], 'report_type': 'pdf'})

class ManyToOneFieldDelegate( AbstractFieldDelegate ):
	def __init__(self, parent, attributes):
		AbstractFieldDelegate.__init__(self, parent, attributes)
		self.currentIndex = None
		self.currentEditor = None
		self.currentValue = None

	def createEditor(self, parent, option, index):
		widget = AbstractFieldDelegate.createEditor(self, parent, option, index)
		if widget:
			# Create shortcuts
			self.scNew = QShortcut( widget )
			self.scNew.setContext( Qt.WidgetShortcut )
			self.scNew.setKey( Shortcuts.CreateInField )
			self.connect( self.scNew, SIGNAL('activated()'), self.new )

			self.scSearch = QShortcut( widget )
			self.scSearch.setContext( Qt.WidgetShortcut )
			self.scSearch.setKey( Shortcuts.SearchInField )
			self.connect( self.scSearch, SIGNAL('activated()'), self.open )
		self.currentEditor = widget
		return widget

	def open(self):
		pass

	def new(self):
		dialog = ScreenDialog( self.currentEditor )
		dialog.setAttributes( self.attributes )
		dialog.setup( self.attributes['relation'] )
		if dialog.exec_() == QDialog.Accepted:
			if self.currentIndex and self.currentIndex.isValid():
				# We expect a KooModel here
				model = index.model().modelFromIndex( index )
				model.setValue(self.name, dialog.model)

	def setModelData(self, editor, kooModel, index):
		# We expect a KooModel here
		model = kooModel.modelFromIndex( index )

		if not unicode(editor.text()):
			model.setValue( self.name, False )
			return

		if unicode( kooModel.data( index, Qt.DisplayRole ).toString() ) == unicode( editor.text() ):
			return

		domain = model.domain( self.name )
		context = model.context()
		ids = Rpc.session.execute('/object', 'execute', self.attributes['relation'], 'name_search', unicode( editor.text() ), domain, 'ilike', context)
		if ids and len(ids)==1:
			model.setValue( self.name, ids[0] )
		else:
			dialog = SearchDialog(self.attributes['relation'], sel_multi=False, ids=[x[0] for x in ids], context=context, domain=domain)
			if dialog.exec_() == QDialog.Accepted and dialog.result:
				id = dialog.result[0]
				name = Rpc.session.execute('/object', 'execute', self.attributes['relation'], 'name_get', [id], Rpc.session.context)[0]
				
				# Directly set the value to the model. There's no need to
				# use setData() but we mainly want to workaround a bug in
				# PyQt 4.4.3 and 4.4.4.
				#value = [ QVariant( name[0] ), QVariant( name[1] ) ]
				#kooModel.setData( index, QVariant( value ), Qt.EditRole )
				model.setValue( self.name, name )
