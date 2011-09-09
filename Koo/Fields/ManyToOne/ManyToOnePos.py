##############################################################################
#
# Copyright (c) 2010 Albert Cervera i Areny <albert@nan-tic.com>

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
from Common.Ui import *

from Koo.Common import Api
from Koo.Common import Common
from Koo import Rpc

from Koo.Screen.Screen import Screen
from Koo.Model.Group import RecordGroup
from Koo.Fields.AbstractFieldWidget import *
from Koo.Fields.AbstractFieldDelegate import *
from Koo.Dialogs.SearchDialog import SearchDialog

(ManyToOnePosFieldWidgetUi, ManyToOnePosFieldWidgetBase ) = loadUiType( Common.uiPath('many2one_pos.ui') ) 

class ManyToOnePosFieldWidget(AbstractFieldWidget, ManyToOnePosFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		ManyToOnePosFieldWidgetUi.__init__(self)
		self.setupUi(self)

		self.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Preferred )

		self.connect( self.screen, SIGNAL('currentChanged()'), self.selected )

		self.installPopupMenu( self.screen )
		self.old = None
		self.latestMatch = None
		self.searching = True

	def colorWidget(self):
		view = self.screen.currentView()
		if view:
			return view.widget
		return self.screen

	def initGui(self):
		group = RecordGroup( self.attrs['relation'] )
		group.setDomainForEmptyGroup()


		self.screen.setRecordGroup( group )
		self.screen.setEmbedded( True )
		#self.screen.setViewTypes( ['tree'] )
		# Set the view first otherwise, default values created by self.screen.new()
		# would only be set for those values handled by the current view.
		if 'views' in self.attrs and 'tree' in self.attrs['views']:
			arch = self.attrs['views']['tree']['arch']
			fields = self.attrs['views']['tree']['fields']
			self.screen.addView(arch, fields, display=True)
		else:
			self.screen.addViewByType('tree', display=True)
		treeView = self.screen.currentView().widget
		treeView.setHeaderHidden( True )

	def selected(self):
		id = self.screen.currentId()
		self.record.setValue(self.name, id)

	def setReadOnly(self, value):
		AbstractFieldWidget.setReadOnly(self, value)

	def clear(self):
		self.screen.setCurrentRecord( None )
		#self.screen.display()

	def showValue(self):
		group = self.screen.group 
		group.setContext( self.record.fieldContext( self.name ) )
		domain = self.record.domain( self.name )
		if group.domain() != domain:
			group.setDomain( self.record.domain( self.name ) )

		id = self.record.value(self.name)[0]
		if id:
			record = group.modelById( id )
		else:
			record = None
		self.screen.setCurrentRecord( record )
		self.screen.display()
		# Resize all columns to contents
		treeView = self.screen.currentView().widget
		for column in xrange(0, treeView.model().columnCount()):
			treeView.resizeColumnToContents( column )

	# We do not store anything here as elements are added and removed in the
	# Screen (self.screen). The only thing we need to take care of (as noted 
	# above) is to ensure that the model and field are marked as modified.
	def storeValue(self):
		pass

	def saveState(self):
		self.screen.storeViewSettings()
		return AbstractFieldWidget.saveState(self)

