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
from widget.model.group import ModelRecordGroup

import rpc

from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from modules.gui.window.win_search import SearchDialog

class ManyToManyFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		loadUi( common.uiPath('many2many.ui'), self)
		self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )

		self.colors['normal'] = self.palette().color( self.backgroundRole() )	
		
		self.connect( self.pushAdd, SIGNAL( "clicked()"), self.add )
		self.connect( self.pushRemove, SIGNAL( "clicked()"), self.remove )
		
		#self.screen = Screen(attrs['relation'], view_type=['tree'], parent=self, views_preload=attrs.get('views', {}))
		self.screen = Screen( self )
		self.screen.setModelGroup( ModelRecordGroup( attrs['relation'] ) )
		self.screen.setViewTypes( ['tree'] )
		self.screen.setPreloadedViews( attrs.get('views', {}) )
		self.screen.setEmbedded( True )

		layout = self.layout()
		layout.insertWidget( 1, self.screen )
		self.installPopupMenu( self.uiText )
		self.old = None

	
	def sizeHint( self ):
		return QSize( 200,800 )

	def add(self):
		domain = self.model.domain( self.name )
		context = self.model.fieldContext( self.name )

		ids = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', str( self.uiText.text()), domain, 'ilike', context)
		ids = map(lambda x: x[0], ids)
		if len(ids)<>1:
			dialog = SearchDialog(self.attrs['relation'], sel_multi=True, ids=ids)
			if dialog.exec_() == QDialog.Rejected:
				return
			ids = dialog.result

		self.screen.load(ids)
		self.screen.display()
		self.uiText.clear()

	def remove(self):
		slcIndex =  self.screen.current_view.widget.selectedIndexes()
		id = self.screen.remove()
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
		models = self.model.value(self.name)
		self.screen.setModelGroup(models)
		self.screen.display()

	def store(self):
		#self.model.setValue( self.name, [ x.id for x in self.screen.models.models] )
		self.screen.display()

