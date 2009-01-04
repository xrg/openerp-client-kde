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

from Koo.FieldWidgets.AbstractFieldWidget import *
from Koo.FieldWidgets.AbstractFieldDelegate import *
from Koo.Common import Common
from Screen import Screen
from Koo.Model.Group import ModelRecordGroup

(ScreenDialogUi, ScreenDialogBase) = loadUiType( Common.uiPath('dia_form_win_many2one.ui') ) 

class ScreenDialog( QDialog, ScreenDialogUi ):
	def __init__(self, modelGroup, parent, model=None, attrs={}):
		QDialog.__init__( self, parent )
		ScreenDialogUi.__init__( self )
		self.setupUi( self )

		self.setModal(True)
		if ('string' in attrs) and attrs['string']:
			self.setWindowTitle( self.windowTitle() + " - " + attrs['string'])

		self.screen = Screen( self )
		self.screen.setModelGroup( modelGroup )
		self.screen.setEmbedded( True )
		if not model:
			model = self.screen.new()
		self.screen.setCurrentRecord( model )
		if ('views' in attrs) and ('form' in attrs['views']):
			arch = attrs['views']['form']['arch']
			fields = attrs['views']['form']['fields']
			self.screen.addView(arch, fields, display=True)
		else:
			self.screen.addViewByType('form', display=True)

		self.screen.display()
		self.layout().insertWidget( 0, self.screen )

		self.connect( self.pushOk, SIGNAL("clicked()"), self.accepted )
		self.connect( self.pushCancel, SIGNAL("clicked()"), self.reject )
		
		size = self.screen.sizeHint()
		self.screen.setMinimumSize( size.width(), size.height()+80 )

		self.show()

	def accepted( self ):
		self.screen.currentView().store()
		self.accept()

(OneToManyFormWidgetUi, OneToManyFormWidgetBase ) = loadUiType( Common.uiPath('one2many.ui') ) 

class OneToManyFormWidget(AbstractFormWidget, OneToManyFormWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		OneToManyFormWidgetUi.__init__(self)
		self.setupUi(self)

		self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )

		self.colors['normal'] = self.palette().color( self.backgroundRole() )

		self.connect( self.pushNew, SIGNAL( "clicked()"),self.new )
		self.connect( self.pushEdit,SIGNAL( "clicked()"),self.edit )
		self.connect( self.pushRemove, SIGNAL( "clicked()"),self.remove )
		self.connect( self.pushBack, SIGNAL( "clicked()"),self.previous )
		self.connect( self.pushForward, SIGNAL( "clicked()"),self.next )
		self.connect( self.pushSwitchView, SIGNAL( "clicked()"),self.switchView )

		group = ModelRecordGroup( attrs['relation'] )
		group.makeEmpty()

		self.screen = Screen( self )
		self.screen.setModelGroup( group )
		self.screen.setPreloadedViews( attrs.get('views', {}) )
		self.screen.setEmbedded( True )
		self.screen.setViewTypes( attrs.get('mode', 'tree,form').split(',') )

		self.connect(self.screen, SIGNAL('recordMessage(int,int,int)'), self.setLabel)
		self.connect(self.screen, SIGNAL('activated()'), self.switchView)

		self.layout().insertWidget( 1, self.screen )
		self.uiTitle.setText( self.screen.currentView().title )
		self.installPopupMenu( self.uiTitle )

	def sizeHint( self ):
		return QSize( 200,800 )
	
	def switchView(self):
		self.screen.switchView()

	def setReadOnly(self, value):
 		self.uiTitle.setEnabled( not value )
 		self.pushNew.setEnabled( not value )
 		self.pushEdit.setEnabled( not value )
 		self.pushRemove.setEnabled( not value )
	
	def colorWidget(self):
		return self.screen

	def new(self):
                if ( not self.screen.currentView().showsMultipleRecords() ) or not self.screen.isReadOnly():
			self.screen.new()
		else:
			dialog = ScreenDialog(self.screen.models, parent=self, attrs=self.attrs)
			if dialog.exec_() == QDialog.Accepted:
				self.screen.display()

	def edit(self):
		dialog = ScreenDialog( self.screen.models, parent=self, model=self.screen.currentRecord(), attrs=self.attrs)
		dialog.exec_()
		self.screen.display()

	def next(self ): 
		self.screen.displayNext()

	def previous(self): 
		self.screen.displayPrevious()

	def remove(self): 
		self.screen.remove()

	def setLabel(self, position, count, value):
		name = '_'
		if position >= 0:
			name = str(position + 1)
		line = '(%s/%s)' % (name, count)
		self.uiLabel.setText( line )

	def clear(self):
		self.screen.setCurrentRecord( None )
		self.screen.clear()
		self.screen.display()
		
	def showValue(self):
		models = self.model.value(self.name)
		if self.screen.models != models:
			self.screen.setModelGroup(models)
			if models.count():
				self.screen.setCurrentRecord( models.modelByRow(0) )
		self.screen.display()

	def store(self):
		self.screen.currentView().store()

# We don't allow modifying OneToMany fields but we allow creating the editor
# because otherwise the view is no longer in edit mode and moving from one field
# to another, if there's a OneToMany in the middle the user has to press F2 again
# in the next field.
class OneToManyFieldDelegate( AbstractFieldDelegate ):
	def setEditorData(self, editor, index):
		pass
	def setModelData(self, editor, model, index):
		pass

