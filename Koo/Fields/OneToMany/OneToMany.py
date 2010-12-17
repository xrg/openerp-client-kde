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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from Koo.Dialogs.BatchUpdateDialog import *
from Koo.Dialogs.BatchInsertDialog import *

from Koo.Fields.AbstractFieldWidget import *
from Koo.Fields.AbstractFieldDelegate import *
from Koo.Common import Api
from Koo.Common import Common
from Koo.Common import Shortcuts
from Koo.Screen.Screen import Screen
from Koo.Model.Group import RecordGroup

(OneToManyDialogUi, OneToManyDialogBase) = loadUiType( Common.uiPath('one2many_dialog.ui') ) 

class OneToManyDialog( QDialog, OneToManyDialogUi ):
	def __init__(self, modelGroup, parent, record=None, attrs=None, creationContext=None):
		QDialog.__init__( self, parent )
		OneToManyDialogUi.__init__( self )
		self.setupUi( self )

		if attrs is None:
			attrs = {}
		if creationContext is None:
			creationContext = {}

		self.creationContext = creationContext

		self.setModal(True)
		if ('string' in attrs) and attrs['string']:
			self.setWindowTitle( unicode(self.windowTitle()) + " - " + attrs['string'])

		self.screen.setRecordGroup( modelGroup )
		self.screen.setEmbedded( True )
		# Set the view first otherwise, default values created by self.screen.new()
		# would only be set for those values handled by the current view.
		if ('views' in attrs) and ('form' in attrs['views']):
			arch = attrs['views']['form']['arch']
			fields = attrs['views']['form']['fields']
			self.screen.addView(arch, fields, display=True)
		else:
			self.screen.addViewByType('form', display=True)

		if not record:
			self._recordAdded = True
			record = self.screen.new(context=self.creationContext)
		else:
			self._recordAdded = False
		self.screen.setCurrentRecord( record )

		self.screen.display()

		self.connect( self.pushOk, SIGNAL("clicked()"), self.accepted )
		self.connect( self.pushCancel, SIGNAL("clicked()"), self.rejected )
		self.connect( self, SIGNAL('reject()'), self.cleanup )
		self.connect( self.pushPrevious, SIGNAL('clicked()'), self.previous )
		self.connect( self.pushNext, SIGNAL('clicked()'), self.next )

		if not self._recordAdded:
			# If the user is modifying an existing record, he won't be
			# able to cancel changes so we better hide the Cancel button
			self.pushCancel.hide()
		
		# Make screen as big as needed but ensuring it's not bigger than
		# the available space on screen (minus some pixels so they can be
		# used by dialog).
		size = self.screen.sizeHint()
		available = QDesktopWidget().availableGeometry().size()
		available -= QSize( 180, 180 )
		self.screen.setMinimumSize( size.boundedTo( available ) )

		self.updatePosition()
		self.show()

	def setReadOnly(self, value):
		self.screen.setReadOnly( value )

	def cleanup(self):
		if self._recordAdded:
			self.screen.remove()
		# Ensure there's no current record so a signal in modelGroup doesn't 
		# trigger a updateDisplay in this screen object.
		self.screen.setCurrentRecord( None )

	def rejected( self ):
		self.cleanup()
		self.reject()

	def accepted( self ):
		if self._recordAdded:
			self.screen.currentView().store()
			self.screen.new(context=self.creationContext)
			self.updatePosition()
		else:
			self.screen.currentView().store()
			# Ensure there's no current record so a signal in modelGroup doesn't 
			# trigger a updateDisplay in this screen object.
			self.screen.setCurrentRecord( None )
			self.accept()

	def updatePosition( self ):
		position = self.screen.group.indexOfRecord( self.screen.currentRecord() ) + 1
		total = self.screen.group.count()
		self.uiPosition.setText( '(%s/%s)' % (position, total) )

	def previous( self ):
		self.screen.currentView().store()
		self.screen.displayPrevious()
		self.updatePosition()

	def next( self ):
		self.screen.currentView().store()
		self.screen.displayNext()
		self.updatePosition()

(OneToManyFieldWidgetUi, OneToManyFieldWidgetBase ) = loadUiType( Common.uiPath('one2many.ui') ) 

class OneToManyFieldWidget(AbstractFieldWidget, OneToManyFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		OneToManyFieldWidgetUi.__init__(self)
		self.setupUi(self)

		self.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Expanding )

		# Extra Actions
		self.actionDuplicate = QAction(self)
		self.actionDuplicate.setText( _('&Duplicate Selected Records') )
		self.actionDuplicate.setIcon( QIcon( ':/images/duplicate.png' ) )
		self.connect(self.actionDuplicate, SIGNAL('triggered()'), self.duplicate)

		self.actionBatchInsert = QAction(self)
		self.actionBatchInsert.setText( _('&Insert Several Records at Once') )
		self.actionBatchInsert.setIcon( QIcon( ':/images/new.png' ) )
		self.connect(self.actionBatchInsert, SIGNAL('triggered()'), self.batchInsert)

		self.actionBatchUpdate = QAction(self)
		self.actionBatchUpdate.setText( _('&Modify All Selected Records') )
		self.actionBatchUpdate.setIcon( QIcon( ':/images/edit.png' ) )
		self.connect(self.actionBatchUpdate, SIGNAL('triggered()'), self.batchUpdate)
		
		self.actionsMenu = QMenu( self )
		self.actionsMenu.addAction( self.actionDuplicate )
		self.actionsMenu.addAction( self.actionBatchInsert )
		self.actionsMenu.addAction( self.actionBatchUpdate )
		self.pushActions.setMenu( self.actionsMenu )

		#self.colors['normal'] = self.palette().color( self.backgroundRole() )

		self.connect( self.pushNew, SIGNAL( "clicked()"),self.new )
		self.connect( self.pushEdit,SIGNAL( "clicked()"),self.edit )
		self.connect( self.pushRemove, SIGNAL( "clicked()"),self.remove )
		self.connect( self.pushBack, SIGNAL( "clicked()"),self.previous )
		self.connect( self.pushForward, SIGNAL( "clicked()"),self.next )
		self.connect( self.pushSwitchView, SIGNAL( "clicked()"),self.switchView )

		self.connect(self.screen, SIGNAL('recordMessage(int,int,int)'), self.setLabel)
		self.connect(self.screen, SIGNAL('activated()'), self.edit)

		# Create shortcuts
		self.scNew = QShortcut( self )
		self.scNew.setKey( Shortcuts.NewInOneToMany )
		self.scNew.setContext( Qt.WidgetWithChildrenShortcut )
		self.connect( self.scNew, SIGNAL('activated()'), self.new )

		self.scEdit = QShortcut( self )
		self.scEdit.setKey( Shortcuts.EditInOneToMany )
		self.scEdit.setContext( Qt.WidgetWithChildrenShortcut )
		self.connect( self.scEdit, SIGNAL('activated()'), self.edit )

		self.scDelete = QShortcut( self )
		self.scDelete.setKey( Shortcuts.DeleteInOneToMany )
		self.scDelete.setContext( Qt.WidgetWithChildrenShortcut )
		self.connect( self.scDelete, SIGNAL('activated()'), self.remove )

		self.scSwitchView = QShortcut( self )
		self.scSwitchView.setKey( Shortcuts.SwitchViewInOneToMany )
		self.scSwitchView.setContext( Qt.WidgetWithChildrenShortcut )
		self.connect( self.scSwitchView, SIGNAL('activated()'), self.switchView )

		# Do not install Popup Menu because setting and getting default values
		# is not supported for OneToMany fields.
		#self.installPopupMenu( self.uiTitle )

	def initGui(self):
		if self.record:
			group = self.record.value(self.name)
		else:
			group = None
		if not group:
			group = RecordGroup( self.attrs['relation'] )
			group.setDomainForEmptyGroup()

		self.screen.setRecordGroup( group )
		self.screen.setPreloadedViews( self.attrs.get('views', {}) )
		self.screen.setEmbedded( True )
		self.screen.setViewTypes( self.attrs.get('mode', 'tree,form').split(',') )
		self.uiTitle.setText( self.screen.currentView().title )

	def duplicate(self):
		for record in self.screen.selectedRecords():
			self.screen.group.duplicate( record )
		self.screen.display()

	def batchUpdate(self):
		dialog = BatchUpdateDialog(self)
		dialog.setIds( self.screen.selectedIds() )
		dialog.setModel( self.screen.resource )
		dialog.setUpdateOnServer( False )
		dialog.setContext( Rpc.session.context )
		dialog.setup( [], [] )
		if dialog.exec_() == QDialog.Rejected:
			return
		for record in self.screen.selectedRecords():
			record.set( dialog.newValues, modified=True )

	def batchInsert(self):
		dialog = BatchInsertDialog(self)
		dialog.setModel( self.screen.resource )
		dialog.setAvailableFields( [x for x in self.screen.group.fields] )
		dialog.setUpdateOnServer( False )
		dialog.setContext( Rpc.session.context )
		if not dialog.setup():
			return
		if dialog.exec_() == QDialog.Rejected:
			return
		for value in dialog.newValues:
			record = self.screen.group.create()
			record.setValue( dialog.newField, value )
		self.screen.display()

	def switchView(self):
		# If Control Key is pressed when the open button is clicked
		# the record will be opened in a new tab. Otherwise it switches
		# view
		if QApplication.keyboardModifiers() & Qt.ControlModifier:
			if not self.screen.currentRecord():
				return
			id = self.screen.currentRecord().id 
			if not id:
				return

			if QApplication.keyboardModifiers() & Qt.ShiftModifier:
				target = 'background'
			else:
				target = 'current'

			Api.instance.createWindow( False, self.attrs['relation'], id, [('id','=',id)], 'form', 
				mode='form,tree', target=target )	
		else:
			self.screen.switchView()

	def setReadOnly(self, value):
		AbstractFieldWidget.setReadOnly(self, value)
 		self.uiTitle.setEnabled( not value )
 		self.pushNew.setEnabled( not value )
 		self.pushRemove.setEnabled( not value )
		self.updateButtons()

	def updateButtons(self):
		if not self.screen.group:
			value = False
		else:
			value = True
 		self.pushEdit.setEnabled( value )
		self.pushBack.setEnabled( value )
		self.pushForward.setEnabled( value )
		self.pushSwitchView.setEnabled( value )

	def colorWidget(self):
		return self.screen

	def new(self):
		# As the 'new' button modifies the model we need to be sure all other fields/widgets
		# have been stored in the model. Otherwise the recordChanged() triggered by calling new
		# in the parent model could make us lose changes.
		self.view.store()
		
		ctx = self.record.evaluateExpression(self.attrs.get('default_get', {}))
		ctx.update(self.record.evaluateExpression( 'dict(%s)' % self.attrs.get('context', '')))

                if ( not self.screen.currentView().showsMultipleRecords() ) or not self.screen.currentView().isReadOnly():
			self.screen.new(context=ctx)
		else:
			dialog = OneToManyDialog(self.screen.group, parent=self, attrs=self.attrs, creationContext=ctx)
			dialog.exec_()
			self.screen.display()

	def edit(self):
		if not self.screen.currentRecord():
			QMessageBox.information(self, _('Information'), _('No record selected'))
			return
		dialog = OneToManyDialog( self.screen.group, parent=self, record=self.screen.currentRecord(), attrs=self.attrs)
		dialog.setReadOnly( self.isReadOnly() )
		dialog.exec_()
		self.screen.display()

	def next(self ): 
		self.screen.displayNext()

	def previous(self): 
		self.screen.displayPrevious()

	def remove(self): 
		# As the 'remove' button modifies the model we need to be sure all other fields/widgets
		# have been stored in the model. Otherwise the recordChanged() triggered by calling remove
		# in the parent model could make us lose changes.
		self.view.store()
		self.screen.remove()

	def setLabel(self, position, count, value):
		name = '_'
		if position >= 0:
			name = str(position + 1)
		line = '(%s/%s)' % (name, count)
		self.uiLabel.setText( line )

	def clear(self):
		self.screen.setRecordGroup( None )
		self.screen.display()
		
	def showValue(self):
		group = self.record.value(self.name)
		# Update context
		group.setContext( self.record.fieldContext( self.name ) )
		if self.screen.group != group:
			self.screen.setRecordGroup(group)
			# Do NOT display if self.screen.group == group. Doing so
			# causes a segmentation fault when storing the form if the one2many
			# has an editable list and one item is being edited.
			self.screen.display()
		self.updateButtons()

	def storeValue(self):
		self.screen.currentView().store()

	def saveState(self):
		self.screen.storeViewSettings()
		return AbstractFieldWidget.saveState(self)

# We don't allow modifying OneToMany fields but we allow creating the editor
# because otherwise the view is no longer in edit mode and moving from one field
# to another, if there's a OneToMany in the middle the user has to press F2 again
# in the next field.
class OneToManyFieldDelegate( AbstractFieldDelegate ):
	def setEditorData(self, editor, index):
		pass
	def setModelData(self, editor, model, index):
		pass

