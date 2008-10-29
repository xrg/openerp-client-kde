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

from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

import gettext
from Koo.Common import Common
from Screen import Screen
from Koo.Model.Group import ModelRecordGroup

class ScreenDialog( QDialog ):
	def __init__(self, modelGroup, parent, model=None, attrs={}):
		QDialog.__init__( self, parent )
		loadUi( Common.uiPath('dia_form_win_many2one.ui'), self )
		self.setModal(True)
		if ('string' in attrs) and attrs['string']:
			self.setWindowTitle( self.windowTitle() + " - " + attrs['string'])

		self.screen = Screen( self )
		self.screen.setModelGroup( modelGroup )
		self.screen.setEmbedded( True )
		if not model:
			model = self.screen.new()
		self.screen.current_model = model
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

		self.result = None
		self.show()

	def accepted( self ):
		self.screen.current_view.store()
		self.result = self.screen.current_model
		self.accept()

class OneToManyFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		loadUi( Common.uiPath('one2many.ui'), self )
		self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )

		self.colors['normal'] = self.palette().color( self.backgroundRole() )

		self.connect( self.pushNew, SIGNAL( "clicked()"),self.new )
		self.connect( self.pushEdit,SIGNAL( "clicked()"),self.edit )
		self.connect( self.pushRemove, SIGNAL( "clicked()"),self.remove )
		self.connect( self.pushBack, SIGNAL( "clicked()"),self.previous )
		self.connect( self.pushForward, SIGNAL( "clicked()"),self.next )
		self.connect( self.pushSwitchView, SIGNAL( "clicked()"),self.switchView )

		self.screen = Screen( self )
		self.screen.setModelGroup( ModelRecordGroup( attrs['relation'] ) )
		self.screen.setPreloadedViews( attrs.get('views', {}) )
		self.screen.setEmbedded( True )
		self.screen.setAddAfterNew( True )
		self.screen.setViewTypes( attrs.get('mode', 'tree,form').split(',') )

		self.connect(self.screen, SIGNAL('recordMessage(int,int,int)'), self.setLabel)
		self.connect(self.screen, SIGNAL('activated()'), self.switchView)

		self.layout().insertWidget( 1, self.screen )
		self.uiTitle.setText( self.screen.current_view.title )
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
                if (self.screen.current_view.view_type=='form') or not self.screen.isReadOnly():
			self.screen.new()
		else:
			dialog = ScreenDialog(self.screen.models, parent=self, attrs=self.attrs)
			if dialog.exec_() == QDialog.Accepted:
				self.screen.display()

	def edit(self):
		dialog = ScreenDialog( self.screen.models, parent=self, model=self.screen.current_model, attrs=self.attrs)
		dialog.exec_()
		self.screen.display()

	def next(self ): 
		self.screen.display_next()

	def previous(self): 
		self.screen.display_prev()

	def remove(self): 
		self.screen.remove()

	def setLabel(self, position, count, value):
		name = '_'
		if position >= 0:
			name = str(position + 1)
		line = '(%s/%s)' % (name, count)
		self.uiLabel.setText( line )

	def clear(self):
		self.screen.current_model = None
		self.screen.clear()
		self.screen.display()
		
	def showValue(self):
		models = self.model.value(self.name)
		if self.screen.models != models:
			self.screen.setModelGroup(models)
			if models.count():
				self.screen.current_model = models.modelByRow(0)
		self.screen.display()

	def store(self):
		self.screen.current_view.store()
