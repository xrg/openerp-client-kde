##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: many2many.py 3076 2006-05-03 17:34:38Z pinky $
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

from common import common

from widget.screen import Screen

import rpc

from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from modules.gui.window.win_search import win_search

class many2many(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		loadUi( common.uiPath('many2many.ui'), self)

		self.colors['normal'] = self.palette().color( self.backgroundRole() )	
		
		self.connect( self.pushAdd, SIGNAL( "clicked()"), self.slotAdd )
		self.connect( self.pushRemove, SIGNAL( "clicked()"), self.slotRemove )
		
		self.screen = Screen(attrs['relation'], view_type=['tree'],parent=self, views_preload=attrs.get('views', {}), tree_saves=False, create_new=True )

		layout = self.layout()
		layout.insertWidget( 1, self.screen )
		self.uiText.installEventFilter( self )
		self.old = None
		self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )

	
	#def eventFilter( self, target, event):
	#	if event.type() == QEvent.MouseButtonPress:
	#		return self.showPopupMenu( target, event )
	#	return False

	def sizeHint( self ):
		return QSize( 200,800 )

	#def _menu_sig_default_set(self):
	#	self.set_value(self.modelfield)
	#	return super(many2many, self)._menu_sig_default_set()

	#def _menu_sig_default(self, obj):
	#	res = rpc.session.execute('/object', 'execute', self.attrs['model'], 'default_get', [self.attrs['name']])
	#	self.value = res.get(self.attrs['name'], False)

	def slotAdd(self):
		domain = self.model.domain( self.name )
		context = self.model.fieldContext( self.name )

		ids = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', str( self.uiText.text()), domain, 'ilike', context)
		ids = map(lambda x: x[0], ids)
		if len(ids)<>1:
			win = win_search(self.attrs['relation'], sel_multi=True, ids=ids)
			win.exec_()
			ids = win.result

		self.modified()
		self.screen.load(ids)
		self.screen.display()
		self.uiText.setText('')

	def slotRemove(self):
		slcIndex =  self.screen.current_view.widget.selectedIndexes()
		id = self.screen.remove(  )
		self.screen.display()

	def setReadOnly(self, ro):
		self.uiText.setEnabled( not ro )
		self.pushAdd.setEnabled( not ro )
		self.pushRemove.setEnabled( not ro )

	def clear(self):
		self.screen.current_model = None
		self.uiText.setText('')
		self.screen.clear()	
		self.screen.display()

	def showValue(self):
		ids = []
		ids = self.model.value(self.name)
		if ids<>self.old:
			self.screen.clear()
			self.screen.load(ids)
			self.old = ids
		self.screen.display()

	def store(self):
		self.model.setValue( self.name, [ x.id for x in self.screen.models.models] )

