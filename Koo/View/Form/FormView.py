 ##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from Koo.Common import Common
from Koo import Rpc

from Koo.View.AbstractView import *
from Koo.FieldWidgets.AbstractFieldWidget import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class FormContainer( QWidget ):
	def __init__(self, parent=None, maxColumns=4):
		QWidget.__init__(self, parent)
		self.row = 0
		self.column = 0
		self.layout = QGridLayout( self )
		self.maxColumns = maxColumns
		self.hasExpanding = False

	def showHelp(self, link):
		QApplication.postEvent( self.sender(), QEvent( QEvent.WhatsThis ) )

	def addWidget(self, widget, attributes={}, labelText=None):
		colspan = int(attributes.get( 'colspan', 1 ))
		helpText = attributes.get( 'help', False )
		stylesheet = attributes.get( 'stylesheet', False )

		if colspan > self.maxColumns:
			colspan = self.maxColumns
			
		a = labelText and 1 or 0
		if colspan + self.column + a  > self.maxColumns:
			self.newRow()

		if labelText:
			label  = QLabel( self )
			label.setText( unicode( labelText ) )
			label.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
			label.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
			if helpText:
				label.setText( unicode( '<small><a href="help">?</a></small> ' + labelText ) )
				label.setToolTip( '<b>%s</b><br/>%s' % (labelText, helpText) )
				label.setWhatsThis( helpText )
				self.connect( label, SIGNAL('linkActivated(QString)'), self.showHelp )

			self.layout.addWidget( label, self.row, self.column )
			self.column = self.column + 1

		self.layout.addWidget( widget, self.row, self.column, 1, colspan )
		if widget.sizePolicy().verticalPolicy() == QSizePolicy.Expanding:
			self.hasExpanding = True

		if stylesheet:
			widget.setStyleSheet( stylesheet )
		self.column = self.column + colspan

	def newRow(self):
		# Here we try to find out if any of the widgets in the row
		# we have just created is trying to expand. If so then any
		# FormContainers in this new row (that don't have hasExpanding)
		# need to be expanded.
		#
		# Supose you have in the same row a OneToMany widget (which expands) 
		# and a Group (Which is a FormContainer) with two buttons. In this
		# case you need to add a spacer at the end of the Group. However,
		# if non of the widgets of the row is Expanding then you need NOT
		# to add the spacer at the end of the group as this would make the
		# whole row try to get more space.
		#
		# The following screens have served for testing: Invoices, Requests
		# and timesheets. All have examples of groups in a row in which there
		# are other widgets (expanding and non-expanding ones).
		containers = []
		expands = False
		for x in range(self.layout.count()):
			pos = self.layout.getItemPosition( x )
			if pos[1] != self.row: 
				continue
			w = self.layout.itemAt( x ).widget()
			if isinstance(w, FormContainer) and not w.hasExpanding:
				containers.append( w )
			elif w.sizePolicy().verticalPolicy() == QSizePolicy.Expanding:
				expands = True
		for x in containers:
			x.expand()

		self.row = self.row + 1
		self.column = 0

	def expand(self):
		if self.hasExpanding:
			return
		self.layout.addItem( QSpacerItem( 0, 1, QSizePolicy.Fixed, QSizePolicy.Expanding ), self.row+1, 0 )

class FormView( AbstractView ):
	def __init__(self, parent=None):
		AbstractView.__init__( self, parent )
		# We still depend on the parent being a screen because of ButtonFormWidget
		self.screen = parent
		self.view_type = 'form'
		self.title = ""
		self.model = None

		self.layout = QHBoxLayout( self )
		self.layout.setContentsMargins( 0, 0, 0, 0 )

		# The parser will include all the widgets here with {name: widget} structure
		self.widgets = {}

	def setWidget(self, widget):
		self.widget = widget
		self.layout.addWidget( self.widget, 10 )

	def __getitem__(self, name):
		return self.widgets[name]
	
	def store(self):
		if not self.model:
			return
		
		for name in self.widgets:
			if self.widgets[name].model:
				self.widgets[name].store()
			else:
				# TODO: Why should this happen?
				print "NO MODEL SET FOR WIDGET: ", name

	def selectedIds(self):
		if self.model:
			return [self.model.id]
		return []

	def reset(self):
		for name, widget in self.widgets.items():
			widget.reset()

	def display(self, currentModel, models):
		self.model = currentModel
		self.updateDisplay(self.model)

	def updateDisplay(self,model):
		if self.model and ('state' in self.model.mgroup.fields):
			state = self.model.value('state')
		else:
			state = 'draft'
		for name in self.widgets:
			if self.model:
				self.widgets[name].load(self.model, state)
			else:
				self.widgets[name].load(None, state)
		 
	def viewSettings(self):
		splitters = self.findChildren( QSplitter )
		data = QByteArray()
		stream = QDataStream( data, QIODevice.WriteOnly )
		for x in splitters:
			stream << x.saveState()
		return str( data.toBase64() )

	def setViewSettings(self, settings):
		if not settings:
			return
		splitters = self.findChildren( QSplitter )
		data = QByteArray.fromBase64( settings )
		stream = QDataStream( data )
		for x in splitters:
			if stream.atEnd():
				return
			value = QByteArray()
			stream >> value
			x.restoreState( value )

	def showsMultipleRecords(self):
		return False
