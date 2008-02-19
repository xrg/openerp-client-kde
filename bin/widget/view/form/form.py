 ##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: form.py 4698 2006-11-27 12:30:44Z ced $
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
import rpc
import service

from widget.view.abstractview import *
from  abstractformwidget import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import traceback

class FormContainer( QWidget ):
	def __init__(self, parent=None, maxColumns=4):
		QWidget.__init__(self, parent)
		self.row = 0
		self.column = 0
		self.layout = QGridLayout( self )
		self.maxColumns = maxColumns
		self.hasExpanding = False

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
			label  = QLabel( unicode( labelText ), self )
			label.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
			label.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
			if helpText:
				label.setToolTip( helpText )
			self.layout.addWidget( label, self.row, self.column )
			self.column = self.column + 1

		self.layout.addWidget( widget, self.row, self.column, 1, colspan )
		if widget.sizePolicy().verticalPolicy() == QSizePolicy.Expanding:
			self.hasExpanding = True
			#print "HAS EXPANDING!!!"
			#print attributes

		if stylesheet:
			widget.setStyleSheet( stylesheet )
		self.column = self.column + colspan

	def newRow(self):
		self.row = self.row + 1
		self.column = 0

	def expand(self):
		if self.hasExpanding:
			#print "ALREADY HAD EXPANDING!"
			return
		self.layout.addItem( QSpacerItem( 0, 1, QSizePolicy.Fixed, QSizePolicy.Expanding ), self.row+1, 0 )
		#print "ADDED SPACER!"

class ViewForm( AbstractView ):
	def __init__(self, parent=None):
		AbstractView.__init__( self, parent )
		self.view_type = 'form'
		self.model_add_new = False
		self.title = ""
		self.model = None

		self.layout = QHBoxLayout( self )
		self.layout.setContentsMargins( 0, 0, 0, 0 )

		# The parser will append all the buttons here
		self.buttons = []		
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
				# TODO: Why does this happen?
				print "NO MODEL SET FOR WIDGET: ", name

	def selectedIds(self):
		if self.model:
			return [self.model.id]
		return []

	def reset(self):
		for wid_name, widget in self.widgets.items():
			widget.reset()

	def display(self, currentModel, models):
		self.model = currentModel

		if self.model and ('state' in self.model.mgroup.fields):
			#state = self.model['state'].get(self.model)
			state = self.model.value('state')
		else:
			state = 'draft'
		for name in self.widgets:
			if self.model:
				self.widgets[name].load(self.model, state)
			else:
				self.widgets[name].load(None, state)
				
		for button in self.buttons: 
			button.setState(state)

