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
from Koo.Fields.AbstractFieldWidget import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

## @brief The FormContainer class is a widget with some functionalities to help
# the parser construct a Form.
class FormContainer( QWidget ):
	def __init__(self, parent=None, maxColumns=4):
		QWidget.__init__(self, parent)
		self.row = 0
		self.column = 0
		self.layout = QGridLayout( self )
		self.layout.setContentsMargins( 0, 0, 0, 0 )
		self.layout.setVerticalSpacing( 0 )
		self.layout.setAlignment( Qt.AlignTop )
		self.maxColumns = maxColumns
		self.isTab = False
		self.tabWidget = parent

	def setTabEnabled(self, value):
		self.tabWidget.setTabEnabled( self.tabWidget.indexOf( self ), value )

	def showHelp(self, link):
		QApplication.postEvent( self.sender(), QEvent( QEvent.WhatsThis ) )

	def addWidget(self, widget, attributes={}, labelText=None):
		colspan = int(attributes.get( 'colspan', 1 ))
		helpText = attributes.get( 'help', False )
		stylesheet = attributes.get( 'stylesheet', False )

		if colspan > self.maxColumns:
			colspan = self.maxColumns
			
		a = labelText and 1 or 0
		colspan -= a
		colspan = max(colspan, 1)
		if colspan + self.column + a  > self.maxColumns:
			self.newRow()

		if labelText:
			label  = QLabel( self )
			label.setText( unicode( Common.normalizeLabel( labelText ) ) )
			label.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
			label.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
			if helpText:
				helpText = '<b>%s</b><br/>%s' % (labelText, helpText)
				label.setText( unicode( '<small><a href="help">?</a></small> ' + labelText ) )
				label.setToolTip( helpText )
				label.setWhatsThis( helpText )
				widget.setWhatsThis( helpText )
				self.connect( label, SIGNAL('linkActivated(QString)'), self.showHelp )

			self.layout.addWidget( label, self.row, self.column )
			self.column = self.column + 1

		self.layout.addWidget( widget, self.row, self.column, 1, colspan )

		if stylesheet:
			widget.setStyleSheet( stylesheet )
		self.column += colspan

	def newRow(self):
		self.row = self.row + 1
		self.column = 0

## @brief The FormView class is an AbstractView capable of showing one in an read-write form.
class FormView( AbstractView ):
	def __init__(self, parent=None):
		AbstractView.__init__( self, parent )
		# We still depend on the parent being a screen because of ButtonFormWidget
		self.screen = parent
		self.title = ""
		self.record = None
		self._readOnly = False

		self.layout = QHBoxLayout( self )
		self.layout.setContentsMargins( 0, 0, 0, 0 )
		self.layout.setAlignment( Qt.AlignTop )

		# The parser will include all the widgets here with {name: widget} structure
		self.widgets = {}
		# The parser will include here all widgets that can change their state (such as visibility).
		# This can include field widgets but also tabs, and others.
		self.stateWidgets = []

	def viewType(self):
		return 'form'

	def setWidget(self, widget):
		self.widget = widget
		self.layout.addWidget( self.widget, 10 )

	def __getitem__(self, name):
		return self.widgets[name]
	
	def store(self):
		if not self.record:
			return
		
		for name in self.widgets:
			if self.widgets[name].record:
				self.widgets[name].store()
			else:
				# TODO: Why should this happen?
				print "NO MODEL SET FOR WIDGET: ", name

	def selectedRecords(self):
		if self.record:
			return [self.record]
		return []

	def reset(self):
		for name, widget in self.widgets.items():
			widget.reset()

	def display(self, currentRecord, records):
		# Though it might seem it's not necessary to connect FormView to recordChanged signal it
		# actually is. This is due to possible 'on_change' events triggered by the modification of
		# a field. This forces those widgets that might change the record before a 'lostfocus' has been
		# triggered to ensure the view has saved all its fields. As an example, modifying a char field
		# and pressing the new button of a OneToMany widget might trigger a recordChanged before 
		# char field has actually changed the value in the record. After updateDisplay, char field will
		# be reset to its previous state. Take a look at OneToMany implementation to see what's needed
		# in such buttons.
		if self.record:
			self.disconnect(self.record,SIGNAL('recordChanged(PyQt_PyObject)'),self.updateDisplay)
			self.disconnect(self.record,SIGNAL('setFocus(QString)'),self.setFieldFocus)
		self.record = currentRecord
		if self.record:
			self.connect(self.record,SIGNAL('recordChanged(PyQt_PyObject)'),self.updateDisplay)
			self.connect(self.record,SIGNAL('setFocus(QString)'),self.setFieldFocus)
		self.updateDisplay(self.record)

	def setFieldFocus(self, fieldName):
		fieldName = unicode( fieldName )
		if not fieldName in self.widgets:
			return
		self.widgets[fieldName].setFocus()

	def updateDisplay(self, record):

		# Update data on widgets
		for name in self.widgets:
			self.widgets[name].setReadOnly( False )
			if self.record:
				self.widgets[name].load(self.record)
			else:
				self.widgets[name].load(None)

		# Update state widgets
		for widget in self.stateWidgets:
			# Consider 'attrs' attribute
			for attribute, condition in widget['attributes'].iteritems():
				if self.record:
					value = self.record.evaluateCondition( condition )
				else:
					value = False
				if attribute == 'invisible':
					self.setWidgetVisible( widget['widget'], not value )
				elif attribute == 'readonly':
					self.setWidgetReadOnly( widget['widget'], value )
			# Consider 'states' attribute
			if widget['states']:
				if self.record and self.record.fieldExists('state'):
					state = self.record.value('state')
				else:
					state = ''
				if state in widget['states']:
					self.setWidgetVisible( widget['widget'], True )
				else:
					self.setWidgetVisible( widget['widget'], False )

		if self._readOnly:
			for name in self.widgets:
				self.widgets[name].setReadOnly( True )

	def setWidgetVisible(self, widget, value):
		# We need to know if the widget is a FormContainer and it's the
		# main widget in a tab in which case we'll want to disable
		# the whole tab (we can't hide it because Qt doesn't provide an
		# easy way of doing it).
		if isinstance(widget, FormContainer) and widget.isTab:
			widget.setTabEnabled( value )
		else:
			widget.setVisible( value )

	def setWidgetReadOnly(self, widget, value):
		# We need to know if the widget is a FormContainer and it's the
		# main widget in a tab in which case we'll want to disable
		# the whole tab 
		if isinstance(widget, FormContainer) and widget.isTab:
			widget.setTabEnabled( not value )
		else:
			widget.setEnabled( not value )

	def addStateWidget(self, widget, attributes, states):
		if not attributes:
			attributes = "{}"
		attributes = eval( attributes )
		if states:
			states = states.split(',')
		else:
			states = []
		self.stateWidgets.append({
			'widget': widget,
			'attributes': attributes,
			'states': states
		})

	def setReadOnly(self, value):
		self._readOnly = value

	def viewSettings(self):
		splitters = self.findChildren( QSplitter )
		data = QByteArray()
		stream = QDataStream( data, QIODevice.WriteOnly )
		for x in splitters:
			stream << x.saveState()
		for x in sorted( self.widgets.keys() ):
			stream << self.widgets[x].saveState()
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
		for x in sorted( self.widgets.keys() ):
			if stream.atEnd():
				return
			value = QByteArray()
			stream >> value
			self.widgets[x].restoreState( value )

	def showsMultipleRecords(self):
		return False
