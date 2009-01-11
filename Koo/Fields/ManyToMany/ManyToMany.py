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

from Koo.Common import Api
from Koo.Common import Common
from Koo import Rpc

from Koo.Screen.Screen import Screen
from Koo.Model.Group import ModelRecordGroup
from Koo.Fields.AbstractFieldWidget import *
from Koo.Fields.AbstractFieldDelegate import *
from Koo.Dialogs.SearchDialog import SearchDialog

(ManyToManyFieldWidgetUi, ManyToManyFieldWidgetBase ) = loadUiType( Common.uiPath('many2many.ui') ) 

class ManyToManyFieldWidget(AbstractFieldWidget, ManyToManyFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		ManyToManyFieldWidgetUi.__init__(self)
		self.setupUi(self)

		self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )

		self.colors['normal'] = self.palette().color( self.backgroundRole() )	
		
		self.connect( self.pushAdd, SIGNAL( "clicked()"), self.add )
		self.connect( self.pushRemove, SIGNAL( "clicked()"), self.remove )
		self.connect( self.uiText, SIGNAL( 'returnPressed()' ), self.add )

		group = ModelRecordGroup( attrs['relation'] )
		group.makeEmpty()
		
		self.screen = Screen( self )
		self.screen.setModelGroup( group )
		self.screen.setViewTypes( ['tree'] )
		self.screen.setEmbedded( True )
		self.connect( self.screen, SIGNAL('activated()'), self.open )

		layout = self.layout()
		layout.insertWidget( 1, self.screen )
		self.installPopupMenu( self.uiText )
		self.old = None

	def open( self ):
		if not self.screen.currentRecord():
			return
		id = self.screen.currentRecord().id 
		if not id:
			return
		Api.instance.createWindow(False, self.attrs['relation'], id, [], 'form', mode='form,tree')	
	
	def sizeHint( self ):
		return QSize( 200,800 )

	def add(self):
		# As the 'add' button modifies the model we need to be sure all other fields/widgets
		# have been stored in the model. Otherwise the recordChanged() triggered 
		# could make us lose changes.
		self.view.store()

		domain = self.model.domain( self.name )
		context = self.model.fieldContext( self.name )

		ids = Rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', unicode( self.uiText.text()), domain, 'ilike', context)
		ids = [x[0] for x in ids] 
		if len(ids) != 1:
			dialog = SearchDialog(self.attrs['relation'], sel_multi=True, ids=ids)
			if dialog.exec_() == QDialog.Rejected:
				return
			ids = dialog.result

		self.screen.load(ids)
		self.screen.display()
		self.uiText.clear()
		# Manually set the current model and field as modified
		# This is not necessary in case of removing an item. 
		# Maybe a better option should be found. But this one works just right.
		self.screen.models.recordChanged( None )

	def remove(self):
		# As the 'remove' button modifies the model we need to be sure all other fields/widgets
		# have been stored in the model. Otherwise the recordChanged() triggered 
		# could make us lose changes.
		self.view.store()
		self.screen.remove()
		self.screen.display()

	def setReadOnly(self, ro):
		self.uiText.setEnabled( not ro )
		self.pushAdd.setEnabled( not ro )
		self.pushRemove.setEnabled( not ro )

	def clear(self):
		self.screen.setCurrentRecord( None )
		self.uiText.setText('')
		self.screen.clear()	
		self.screen.display()

	def showValue(self):
		models = self.model.value(self.name)
		self.screen.setModelGroup(models)
		self.screen.display()

	# We do not store anything here as elements are added and removed in the
	# Screen (self.screen). The only thing we need to take care of (as noted 
	# above) is to ensure that the model and field are marked as modified.
	def store(self):
		pass

class ManyToManyFieldDelegate( AbstractFieldDelegate ):
	def setModelData(self, editor, kooModel, index):
		if unicode( editor.text() ) == unicode( index.data( Qt.DisplayRole ).toString() ):
			return
		# We expecte a KooModel here
		model = kooModel.modelFromIndex( index )

		#model.setData( index, QVariant( editor.currentText() ), Qt.EditRole )
		domain = model.domain( self.name )
		context = model.fieldContext( self.name )

		ids = Rpc.session.execute('/object', 'execute', self.attributes['relation'], 'name_search', unicode( editor.text() ), domain, 'ilike', context)
		ids = [x[0] for x in ids] 
		if len(ids) != 1:
			dialog = SearchDialog(self.attributes['relation'], sel_multi=True, ids=ids)
			if dialog.exec_() == QDialog.Rejected:
				return
			ids = dialog.result

		ids = [QVariant(x) for x in ids]
		kooModel.setData( index, QVariant(ids), Qt.EditRole )

