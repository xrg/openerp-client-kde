##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: one2many.py 4773 2006-12-05 11:01:20Z ced $
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
from common import common
from widget.screen import Screen

class ScreenDialog( QDialog ):
	def __init__(self, model_name, parent, model=None, attrs={}):
		QDialog.__init__( self, parent )
		loadUi( common.uiPath('dia_form_win_many2one.ui'), self )
		self.setModal(True)
		if ('string' in attrs) and attrs['string']:
			self.setWindowTitle( self.windowTitle() + " - " + attrs['string'])

		self.screen = Screen(model_name, view_type=[], parent=self)
		if not model:
			model = self.screen.new()
		self.screen.models.addModel(model)
		self.screen.current_model = model
		if ('views' in attrs) and ('form' in attrs['views']):
			arch = attrs['views']['form']['arch']
			fields = attrs['views']['form']['fields']
			self.screen.add_view(arch, fields, display=True)
		else:
			self.screen.add_view_id(False, 'form', display=True)

		self.screen.display()
		self.layout().insertWidget( 0, self.screen )

		self.connect( self.pushOk, SIGNAL("clicked()"), self.slotAccepted )
		self.connect( self.pushCancel, SIGNAL("clicked()"), self.close )
		
		size = self.screen.size()
		self.setMinimumSize( size.width(), size.height()+30)

		self.show()

##	def new(self):
#		model = self.screen.new()
#		self.screen.models.model_add(model)
#		self.screen.current_model = model
#		return True

	def slotAccepted( self ):
		self.screen.current_view.store()
		model = self.screen.current_model
		self.result = ( True, model )
		self.accept()

class OneToManyFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		loadUi( common.uiPath('one2many.ui'), self )

		self.colors['normal'] = self.palette().color( self.backgroundRole() )

		self.connect( self.pushNew, SIGNAL( "clicked()"),self._sig_new )
		self.connect( self.pushEdit,SIGNAL( "clicked()"),self._sig_edit)
		self.connect( self.pushRemove, SIGNAL( "clicked()"),self._sig_remove)
		self.connect( self.pushBack, SIGNAL( "clicked()"),self._sig_previous )
		self.connect( self.pushForward, SIGNAL( "clicked()"),self._sig_next )
		self.connect( self.pushSwitchView, SIGNAL( "clicked()"),self.switchView )

 		self.screen = Screen(attrs['relation'], view_type=attrs.get('mode','tree,form').split(','), parent=self, views_preload=attrs.get('views', {}), tree_saves=False, create_new=True)
 		
		self.connect(self.screen, SIGNAL('recordMessage(int,int,int)'), self.setLabel)

		self.layout().insertWidget( 1, self.screen )
		self.uiTitle.insertItem( 0, self.screen.current_view.title )
		self.uiTitle.setCurrentIndex( 0 )
		self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )

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

	def _sig_new(self):
                if (self.screen.current_view.view_type=='form') or not self.screen.readOnly():
			self.screen.new()
		else:
			ok = 1
			dia = ScreenDialog(self.attrs['relation'], parent=self, attrs=self.attrs) 
			dia.exec_()
			ok, value = dia.result
			if ok:
				self.screen.models.addModel(value)
				self.screen.display()

	def _sig_edit(self):
		dia = ScreenDialog(self.attrs['relation'], parent=self, model=self.screen.current_model, attrs=self.attrs)
		ok = dia.exec_()
		if ok == 1:
			ok,value = dia.result
		self.screen.display()

	def _sig_next(self ): 
		self.screen.display_next()

	def _sig_previous(self): 
		self.screen.display_prev()

	def _sig_remove(self): 
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
		self.screen.setModels(models)
		self.screen.display()

	def store(self):
		self.screen.current_view.store()
